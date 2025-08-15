#!/usr/bin/env python3
"""
Testes de Integração Completos
Sistema de Pré-processamento de PDF com Descrição de Imagens

Este módulo contém todos os testes de integração do sistema.
"""

import os
import sys
import time
import json
import requests
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pytest
import asyncio
from dataclasses import dataclass

@dataclass
class TestResult:
    """Resultado de um teste."""
    name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    error: Optional[str] = None

class IntegrationTester:
    """Classe principal para testes de integração."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8099"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        
        self.test_results: List[TestResult] = []
        self.test_files = self._discover_test_files()
        
    def _discover_test_files(self) -> List[Path]:
        """Descobre arquivos PDF para teste."""
        pdf_files = []
        if self.data_dir.exists():
            pdf_files = list(self.data_dir.glob("*.pdf"))
        
        return pdf_files
    
    def log(self, message: str, level: str = "INFO"):
        """Registra mensagem."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [INTEGRATION] [{level}] {message}")
    
    def measure_time(self, func):
        """Decorator para medir tempo de execução."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            return result, duration
        return wrapper
    
    def test_server_health(self) -> TestResult:
        """Testa saúde do servidor."""
        self.log("Testando saúde do servidor...")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/")
            duration = time.time() - start_time
            
            success = response.status_code == 200
            details = {
                "status_code": response.status_code,
                "response_time_ms": round(duration * 1000, 2),
                "content_length": len(response.content)
            }
            
            return TestResult(
                name="server_health",
                success=success,
                duration=duration,
                details=details
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="server_health",
                success=False,
                duration=duration,
                details={},
                error=str(e)
            )
    
    def test_pdf_upload(self, pdf_file: Path) -> TestResult:
        """Testa upload de PDF."""
        self.log(f"Testando upload: {pdf_file.name}")
        start_time = time.time()
        
        try:
            with open(pdf_file, "rb") as f:
                files = {"file": (pdf_file.name, f, "application/pdf")}
                response = self.session.post(f"{self.base_url}/api/upload", files=files)
            
            duration = time.time() - start_time
            success = response.status_code == 200
            
            details = {
                "file_name": pdf_file.name,
                "file_size_mb": round(pdf_file.stat().st_size / (1024*1024), 2),
                "status_code": response.status_code,
                "upload_time_ms": round(duration * 1000, 2)
            }
            
            if success:
                response_data = response.json()
                details.update({
                    "file_id": response_data.get("file_id"),
                    "filename": response_data.get("filename")
                })
            
            return TestResult(
                name=f"upload_{pdf_file.stem}",
                success=success,
                duration=duration,
                details=details,
                error=None if success else response.text
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=f"upload_{pdf_file.stem}",
                success=False,
                duration=duration,
                details={"file_name": pdf_file.name},
                error=str(e)
            )
    
    def test_pdf_extraction(self, file_id: str, filename: str) -> TestResult:
        """Testa extração de conteúdo do PDF."""
        self.log(f"Testando extração: {filename}")
        start_time = time.time()
        
        try:
            response = self.session.post(f"{self.base_url}/api/extract/{file_id}")
            duration = time.time() - start_time
            success = response.status_code == 200
            
            details = {
                "file_id": file_id,
                "filename": filename,
                "status_code": response.status_code,
                "extraction_time_ms": round(duration * 1000, 2)
            }
            
            if success:
                response_data = response.json()
                details.update({
                    "pages_count": len(response_data.get("pages", [])),
                    "tables_count": len(response_data.get("tables", [])),
                    "has_metadata": bool(response_data.get("metadata")),
                    "has_download_url": bool(response_data.get("download", {}).get("zip_url"))
                })
                
                # Contar imagens
                total_images = 0
                for page in response_data.get("pages", []):
                    total_images += len(page.get("images", []))
                details["images_count"] = total_images
            
            return TestResult(
                name=f"extraction_{filename}",
                success=success,
                duration=duration,
                details=details,
                error=None if success else response.text
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=f"extraction_{filename}",
                success=False,
                duration=duration,
                details={"file_id": file_id, "filename": filename},
                error=str(e)
            )
    
    def test_pdf_viewing(self, file_id: str) -> TestResult:
        """Testa visualização do PDF."""
        self.log(f"Testando visualização: {file_id}")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/api/pdf/{file_id}")
            duration = time.time() - start_time
            success = response.status_code == 200
            
            details = {
                "file_id": file_id,
                "status_code": response.status_code,
                "response_time_ms": round(duration * 1000, 2),
                "content_type": response.headers.get("content-type", ""),
                "content_length": len(response.content)
            }
            
            return TestResult(
                name=f"viewing_{file_id}",
                success=success,
                duration=duration,
                details=details,
                error=None if success else response.text
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=f"viewing_{file_id}",
                success=False,
                duration=duration,
                details={"file_id": file_id},
                error=str(e)
            )
    
    def test_image_serving(self, file_id: str, image_name: str) -> TestResult:
        """Testa servir imagens extraídas."""
        self.log(f"Testando imagem: {image_name}")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/api/image/{file_id}/{image_name}")
            duration = time.time() - start_time
            success = response.status_code == 200
            
            details = {
                "file_id": file_id,
                "image_name": image_name,
                "status_code": response.status_code,
                "response_time_ms": round(duration * 1000, 2),
                "content_type": response.headers.get("content-type", ""),
                "image_size_bytes": len(response.content)
            }
            
            return TestResult(
                name=f"image_{image_name}",
                success=success,
                duration=duration,
                details=details,
                error=None if success else response.text
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=f"image_{image_name}",
                success=False,
                duration=duration,
                details={"file_id": file_id, "image_name": image_name},
                error=str(e)
            )
    
    def test_complete_workflow(self, pdf_file: Path) -> List[TestResult]:
        """Testa workflow completo para um PDF."""
        self.log(f"Testando workflow completo: {pdf_file.name}")
        results = []
        
        # 1. Upload
        upload_result = self.test_pdf_upload(pdf_file)
        results.append(upload_result)
        
        if not upload_result.success:
            self.log(f"Upload falhou para {pdf_file.name}, pulando testes subsequentes", "ERROR")
            return results
        
        file_id = upload_result.details.get("file_id")
        filename = upload_result.details.get("filename")
        
        if not file_id:
            self.log(f"file_id não encontrado para {pdf_file.name}", "ERROR")
            return results
        
        # 2. Visualização
        viewing_result = self.test_pdf_viewing(file_id)
        results.append(viewing_result)
        
        # 3. Extração
        extraction_result = self.test_pdf_extraction(file_id, filename)
        results.append(extraction_result)
        
        # 4. Teste de imagens (se houver)
        if extraction_result.success and extraction_result.details.get("images_count", 0) > 0:
            # Testar primeira imagem encontrada
            try:
                # Buscar primeira imagem disponível
                response = self.session.post(f"{self.base_url}/api/extract/{file_id}")
                if response.status_code == 200:
                    data = response.json()
                    for page in data.get("pages", []):
                        images = page.get("images", [])
                        if images:
                            first_image = images[0]
                            image_result = self.test_image_serving(file_id, first_image)
                            results.append(image_result)
                            break
            except Exception as e:
                self.log(f"Erro ao testar imagens: {e}", "ERROR")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes de integração."""
        self.log("🚀 Iniciando testes de integração completos")
        start_time = time.time()
        
        # Teste de saúde do servidor
        health_result = self.test_server_health()
        self.test_results.append(health_result)
        
        if not health_result.success:
            self.log("❌ Servidor não está saudável, abortando testes", "ERROR")
            return self._generate_report()
        
        # Testes com arquivos PDF
        if not self.test_files:
            self.log("⚠️ Nenhum arquivo PDF encontrado para teste", "WARNING")
        else:
            for pdf_file in self.test_files:
                workflow_results = self.test_complete_workflow(pdf_file)
                self.test_results.extend(workflow_results)
        
        total_duration = time.time() - start_time
        self.log(f"✅ Testes concluídos em {total_duration:.2f}s")
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict[str, Any]:
        """Gera relatório dos testes."""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.success])
        failed_tests = total_tests - successful_tests
        
        total_duration = sum(r.duration for r in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": failed_tests,
                "success_rate": round((successful_tests / total_tests * 100), 2) if total_tests > 0 else 0,
                "total_duration": round(total_duration, 2),
                "average_duration": round(avg_duration, 2)
            },
            "test_files": [str(f) for f in self.test_files],
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "duration": round(r.duration, 2),
                    "details": r.details,
                    "error": r.error
                }
                for r in self.test_results
            ]
        }
        
        return report

def main():
    """Função principal para execução standalone."""
    tester = IntegrationTester()
    
    try:
        report = tester.run_all_tests()
        
        # Salvar relatório
        report_file = tester.test_dir / "test_reports" / "integration_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Relatório salvo em: {report_file}")
        print(f"✅ Sucessos: {report['summary']['successful']}")
        print(f"❌ Falhas: {report['summary']['failed']}")
        print(f"📈 Taxa de sucesso: {report['summary']['success_rate']}%")
        
        return report['summary']['failed'] == 0
        
    except Exception as e:
        print(f"💥 Erro durante testes: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
