#!/usr/bin/env python3
"""
Testes de Performance e Carga
Sistema de Pré-processamento de PDF com Descrição de Imagens

Este módulo contém testes de performance, carga e benchmarks.
"""

import os
import sys
import time
import json
import psutil
import threading
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

@dataclass
class PerformanceMetric:
    """Métrica de performance."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int

@dataclass
class BenchmarkResult:
    """Resultado de benchmark."""
    test_name: str
    file_name: str
    file_size_mb: float
    upload_time: float
    extraction_time: float
    total_time: float
    peak_memory_mb: float
    avg_cpu_percent: float
    success: bool
    error: Optional[str] = None

class PerformanceTester:
    """Classe para testes de performance."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8099"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 300  # 5 minutos para testes de performance
        
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.metrics_dir = self.test_dir / "performance_metrics"
        self.metrics_dir.mkdir(exist_ok=True)
        
        self.test_files = self._discover_test_files()
        self.performance_metrics: List[PerformanceMetric] = []
        self.benchmark_results: List[BenchmarkResult] = []
        
        # Configurações de monitoramento
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
    def _discover_test_files(self) -> List[Path]:
        """Descobre arquivos PDF para teste."""
        pdf_files = []
        if self.data_dir.exists():
            pdf_files = list(self.data_dir.glob("*.pdf"))
        return sorted(pdf_files, key=lambda x: x.stat().st_size)
    
    def log(self, message: str, level: str = "INFO"):
        """Registra mensagem."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [PERFORMANCE] [{level}] {message}")
    
    def start_monitoring(self):
        """Inicia monitoramento de recursos."""
        self.monitoring = True
        self.performance_metrics.clear()
        
        def monitor():
            process = psutil.Process()
            net_io_start = psutil.net_io_counters()
            disk_io_start = psutil.disk_io_counters()
            
            while self.monitoring:
                try:
                    # CPU e Memória
                    cpu_percent = process.cpu_percent()
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    
                    # I/O de disco
                    disk_io = psutil.disk_io_counters()
                    disk_read = disk_io.read_bytes - disk_io_start.read_bytes if disk_io else 0
                    disk_write = disk_io.write_bytes - disk_io_start.write_bytes if disk_io else 0
                    
                    # I/O de rede
                    net_io = psutil.net_io_counters()
                    net_sent = net_io.bytes_sent - net_io_start.bytes_sent if net_io else 0
                    net_recv = net_io.bytes_recv - net_io_start.bytes_recv if net_io else 0
                    
                    metric = PerformanceMetric(
                        timestamp=time.time(),
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        disk_io_read=disk_read,
                        disk_io_write=disk_write,
                        network_sent=net_sent,
                        network_recv=net_recv
                    )
                    
                    self.performance_metrics.append(metric)
                    time.sleep(0.5)  # Coleta a cada 500ms
                    
                except Exception as e:
                    self.log(f"Erro no monitoramento: {e}", "ERROR")
                    break
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        self.log("Monitoramento de performance iniciado")
    
    def stop_monitoring(self):
        """Para monitoramento de recursos."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.log("Monitoramento de performance parado")
    
    def benchmark_single_file(self, pdf_file: Path) -> BenchmarkResult:
        """Executa benchmark para um arquivo específico."""
        self.log(f"Benchmark: {pdf_file.name}")
        
        file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
        
        try:
            # Iniciar monitoramento
            self.start_monitoring()
            
            # 1. Upload
            upload_start = time.time()
            with open(pdf_file, "rb") as f:
                files = {"file": (pdf_file.name, f, "application/pdf")}
                upload_response = self.session.post(f"{self.base_url}/api/upload", files=files)
            upload_time = time.time() - upload_start
            
            if upload_response.status_code != 200:
                raise Exception(f"Upload falhou: {upload_response.status_code}")
            
            upload_data = upload_response.json()
            file_id = upload_data["file_id"]
            
            # 2. Extração
            extraction_start = time.time()
            extraction_response = self.session.post(f"{self.base_url}/api/extract/{file_id}")
            extraction_time = time.time() - extraction_start
            
            if extraction_response.status_code != 200:
                raise Exception(f"Extração falhou: {extraction_response.status_code}")
            
            total_time = upload_time + extraction_time
            
            # Parar monitoramento
            self.stop_monitoring()
            
            # Calcular métricas
            if self.performance_metrics:
                peak_memory = max(m.memory_mb for m in self.performance_metrics)
                avg_cpu = sum(m.cpu_percent for m in self.performance_metrics) / len(self.performance_metrics)
            else:
                peak_memory = 0
                avg_cpu = 0
            
            return BenchmarkResult(
                test_name="single_file_benchmark",
                file_name=pdf_file.name,
                file_size_mb=file_size_mb,
                upload_time=upload_time,
                extraction_time=extraction_time,
                total_time=total_time,
                peak_memory_mb=peak_memory,
                avg_cpu_percent=avg_cpu,
                success=True
            )
            
        except Exception as e:
            self.stop_monitoring()
            return BenchmarkResult(
                test_name="single_file_benchmark",
                file_name=pdf_file.name,
                file_size_mb=file_size_mb,
                upload_time=0,
                extraction_time=0,
                total_time=0,
                peak_memory_mb=0,
                avg_cpu_percent=0,
                success=False,
                error=str(e)
            )
    
    def stress_test(self, pdf_file: Path, concurrent_requests: int = 3, iterations: int = 5) -> List[BenchmarkResult]:
        """Executa teste de stress com múltiplas requisições simultâneas."""
        self.log(f"Teste de stress: {pdf_file.name} ({concurrent_requests} concurrent, {iterations} iterations)")
        
        results = []
        
        def single_request(iteration: int) -> BenchmarkResult:
            try:
                start_time = time.time()
                
                # Upload
                with open(pdf_file, "rb") as f:
                    files = {"file": (f"stress_{iteration}_{pdf_file.name}", f, "application/pdf")}
                    upload_response = self.session.post(f"{self.base_url}/api/upload", files=files)
                
                if upload_response.status_code != 200:
                    raise Exception(f"Upload falhou: {upload_response.status_code}")
                
                upload_data = upload_response.json()
                file_id = upload_data["file_id"]
                
                # Extração
                extraction_response = self.session.post(f"{self.base_url}/api/extract/{file_id}")
                
                if extraction_response.status_code != 200:
                    raise Exception(f"Extração falhou: {extraction_response.status_code}")
                
                total_time = time.time() - start_time
                
                return BenchmarkResult(
                    test_name=f"stress_test_req_{iteration}",
                    file_name=pdf_file.name,
                    file_size_mb=pdf_file.stat().st_size / (1024 * 1024),
                    upload_time=0,  # Não medindo separadamente no stress test
                    extraction_time=0,
                    total_time=total_time,
                    peak_memory_mb=0,
                    avg_cpu_percent=0,
                    success=True
                )
                
            except Exception as e:
                return BenchmarkResult(
                    test_name=f"stress_test_req_{iteration}",
                    file_name=pdf_file.name,
                    file_size_mb=pdf_file.stat().st_size / (1024 * 1024),
                    upload_time=0,
                    extraction_time=0,
                    total_time=0,
                    peak_memory_mb=0,
                    avg_cpu_percent=0,
                    success=False,
                    error=str(e)
                )
        
        # Executar requisições concorrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = []
            for i in range(iterations):
                future = executor.submit(single_request, i)
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        return results
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Executa todos os benchmarks de performance."""
        self.log("🚀 Iniciando testes de performance")
        start_time = time.time()
        
        all_results = []
        
        # Benchmark individual para cada arquivo
        for pdf_file in self.test_files:
            result = self.benchmark_single_file(pdf_file)
            all_results.append(result)
            self.benchmark_results.append(result)
            
            # Pequena pausa entre testes
            time.sleep(2)
        
        # Teste de stress com arquivo médio (se disponível)
        if self.test_files:
            # Escolher arquivo do meio da lista (ordenada por tamanho)
            mid_index = len(self.test_files) // 2
            stress_file = self.test_files[mid_index]
            
            stress_results = self.stress_test(stress_file, concurrent_requests=3, iterations=5)
            all_results.extend(stress_results)
            self.benchmark_results.extend(stress_results)
        
        total_duration = time.time() - start_time
        self.log(f"✅ Benchmarks concluídos em {total_duration:.2f}s")
        
        return self._generate_performance_report()
    
    def _generate_performance_report(self) -> Dict[str, Any]:
        """Gera relatório de performance."""
        successful_tests = [r for r in self.benchmark_results if r.success]
        failed_tests = [r for r in self.benchmark_results if not r.success]
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": len(self.benchmark_results),
                "successful": len(successful_tests),
                "failed": len(failed_tests),
                "success_rate": round((len(successful_tests) / len(self.benchmark_results) * 100), 2) if self.benchmark_results else 0
            },
            "performance_stats": {},
            "results": []
        }
        
        if successful_tests:
            # Estatísticas de performance
            upload_times = [r.upload_time for r in successful_tests if r.upload_time > 0]
            extraction_times = [r.extraction_time for r in successful_tests if r.extraction_time > 0]
            total_times = [r.total_time for r in successful_tests if r.total_time > 0]
            memory_usage = [r.peak_memory_mb for r in successful_tests if r.peak_memory_mb > 0]
            
            report["performance_stats"] = {
                "upload_time": {
                    "avg": round(sum(upload_times) / len(upload_times), 2) if upload_times else 0,
                    "min": round(min(upload_times), 2) if upload_times else 0,
                    "max": round(max(upload_times), 2) if upload_times else 0
                },
                "extraction_time": {
                    "avg": round(sum(extraction_times) / len(extraction_times), 2) if extraction_times else 0,
                    "min": round(min(extraction_times), 2) if extraction_times else 0,
                    "max": round(max(extraction_times), 2) if extraction_times else 0
                },
                "total_time": {
                    "avg": round(sum(total_times) / len(total_times), 2) if total_times else 0,
                    "min": round(min(total_times), 2) if total_times else 0,
                    "max": round(max(total_times), 2) if total_times else 0
                },
                "memory_usage_mb": {
                    "avg": round(sum(memory_usage) / len(memory_usage), 2) if memory_usage else 0,
                    "min": round(min(memory_usage), 2) if memory_usage else 0,
                    "max": round(max(memory_usage), 2) if memory_usage else 0
                }
            }
        
        # Adicionar resultados detalhados
        for result in self.benchmark_results:
            report["results"].append({
                "test_name": result.test_name,
                "file_name": result.file_name,
                "file_size_mb": round(result.file_size_mb, 2),
                "upload_time": round(result.upload_time, 2),
                "extraction_time": round(result.extraction_time, 2),
                "total_time": round(result.total_time, 2),
                "peak_memory_mb": round(result.peak_memory_mb, 2),
                "avg_cpu_percent": round(result.avg_cpu_percent, 2),
                "success": result.success,
                "error": result.error
            })
        
        return report
    
    def generate_charts(self, report: Dict[str, Any]):
        """Gera gráficos de performance."""
        try:
            successful_results = [r for r in report["results"] if r["success"]]
            
            if not successful_results:
                self.log("Nenhum resultado bem-sucedido para gerar gráficos", "WARNING")
                return
            
            # Configurar estilo
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Performance Benchmarks - PDF Processing', fontsize=16)
            
            # Gráfico 1: Tempo vs Tamanho do arquivo
            file_sizes = [r["file_size_mb"] for r in successful_results]
            total_times = [r["total_time"] for r in successful_results]
            
            axes[0, 0].scatter(file_sizes, total_times, alpha=0.7)
            axes[0, 0].set_xlabel('File Size (MB)')
            axes[0, 0].set_ylabel('Total Processing Time (s)')
            axes[0, 0].set_title('Processing Time vs File Size')
            
            # Gráfico 2: Distribuição de tempos
            axes[0, 1].hist(total_times, bins=10, alpha=0.7, edgecolor='black')
            axes[0, 1].set_xlabel('Total Processing Time (s)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].set_title('Processing Time Distribution')
            
            # Gráfico 3: Uso de memória
            memory_usage = [r["peak_memory_mb"] for r in successful_results if r["peak_memory_mb"] > 0]
            if memory_usage:
                axes[1, 0].bar(range(len(memory_usage)), memory_usage, alpha=0.7)
                axes[1, 0].set_xlabel('Test Index')
                axes[1, 0].set_ylabel('Peak Memory Usage (MB)')
                axes[1, 0].set_title('Memory Usage by Test')
            
            # Gráfico 4: Comparação Upload vs Extraction
            upload_times = [r["upload_time"] for r in successful_results if r["upload_time"] > 0]
            extraction_times = [r["extraction_time"] for r in successful_results if r["extraction_time"] > 0]
            
            if upload_times and extraction_times:
                x = range(len(upload_times))
                width = 0.35
                axes[1, 1].bar([i - width/2 for i in x], upload_times, width, label='Upload', alpha=0.7)
                axes[1, 1].bar([i + width/2 for i in x], extraction_times, width, label='Extraction', alpha=0.7)
                axes[1, 1].set_xlabel('Test Index')
                axes[1, 1].set_ylabel('Time (s)')
                axes[1, 1].set_title('Upload vs Extraction Time')
                axes[1, 1].legend()
            
            plt.tight_layout()
            
            # Salvar gráfico
            chart_file = self.metrics_dir / "performance_charts.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.log(f"📊 Gráficos salvos em: {chart_file}")
            
        except Exception as e:
            self.log(f"Erro ao gerar gráficos: {e}", "ERROR")

def main():
    """Função principal para execução standalone."""
    tester = PerformanceTester()
    
    try:
        report = tester.run_all_benchmarks()
        
        # Salvar relatório
        report_file = tester.metrics_dir / "performance_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Gerar gráficos
        tester.generate_charts(report)
        
        print(f"\n📊 Relatório salvo em: {report_file}")
        print(f"✅ Sucessos: {report['summary']['successful']}")
        print(f"❌ Falhas: {report['summary']['failed']}")
        print(f"📈 Taxa de sucesso: {report['summary']['success_rate']}%")
        
        if report['performance_stats']:
            stats = report['performance_stats']
            print(f"⏱️ Tempo médio total: {stats['total_time']['avg']}s")
            print(f"💾 Memória média: {stats['memory_usage_mb']['avg']}MB")
        
        return report['summary']['failed'] == 0
        
    except Exception as e:
        print(f"💥 Erro durante benchmarks: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
