#!/usr/bin/env python3
"""
Pipeline de Execução de Testes Finais
Sistema de Pré-processamento de PDF com Descrição de Imagens

Este script orquestra a execução completa dos testes finais.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Importações locais
from server_manager import ServerManager
from integration_tests import IntegrationTester
from performance_tests import PerformanceTester

class TestExecutionPipeline:
    """Pipeline principal de execução de testes."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = Path(__file__).parent
        self.logs_dir = self.test_dir / "logs"
        self.reports_dir = self.test_dir / "test_reports"
        
        # Criar diretórios necessários
        self.logs_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        self.execution_log = self.logs_dir / "execution_pipeline.log"
        
        # Componentes
        self.server_manager = ServerManager()
        self.integration_tester = IntegrationTester()
        self.performance_tester = PerformanceTester()
        
        # Resultados
        self.results = {
            "installation": {},
            "server_startup": {},
            "integration_tests": {},
            "performance_tests": {},
            "summary": {}
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Registra mensagem no log."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [PIPELINE] [{level}] {message}"
        
        print(log_entry)
        with open(self.execution_log, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def check_installation(self) -> bool:
        """Verifica se a instalação está completa."""
        self.log("Verificando instalação...")
        
        try:
            # Verificar se o relatório de instalação existe
            install_report_file = self.test_dir / "installation_report.json"
            if not install_report_file.exists():
                self.log("Relatório de instalação não encontrado. Execute install_pipeline.py primeiro.", "ERROR")
                return False
            
            # Carregar relatório de instalação
            with open(install_report_file, "r", encoding="utf-8") as f:
                install_report = json.load(f)
            
            self.results["installation"] = install_report
            
            if not install_report.get("success", False):
                self.log("Instalação não foi bem-sucedida", "ERROR")
                return False
            
            self.log("✅ Instalação verificada com sucesso")
            return True
            
        except Exception as e:
            self.log(f"Erro ao verificar instalação: {e}", "ERROR")
            return False
    
    def check_environment(self) -> bool:
        """Verifica variáveis de ambiente."""
        self.log("Verificando variáveis de ambiente...")
        
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_CHAT_MODEL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log(f"⚠️ Variáveis de ambiente não configuradas: {missing_vars}", "WARNING")
            self.log("Alguns testes podem falhar sem as configurações do Azure OpenAI", "WARNING")
            return False
        
        self.log("✅ Variáveis de ambiente configuradas")
        return True
    
    def start_test_server(self) -> bool:
        """Inicia servidor de teste."""
        self.log("Iniciando servidor de teste...")
        
        try:
            success = self.server_manager.start_server(timeout=60)
            
            if success:
                status = self.server_manager.get_server_status()
                self.results["server_startup"] = {
                    "success": True,
                    "status": status,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.log("✅ Servidor iniciado com sucesso")
                return True
            else:
                self.results["server_startup"] = {
                    "success": False,
                    "error": "Falha ao iniciar servidor",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.log("❌ Falha ao iniciar servidor", "ERROR")
                return False
                
        except Exception as e:
            self.results["server_startup"] = {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.log(f"💥 Erro ao iniciar servidor: {e}", "ERROR")
            return False
    
    def run_integration_tests(self) -> bool:
        """Executa testes de integração."""
        self.log("🧪 Executando testes de integração...")
        
        try:
            start_time = time.time()
            integration_report = self.integration_tester.run_all_tests()
            duration = time.time() - start_time
            
            self.results["integration_tests"] = integration_report
            self.results["integration_tests"]["execution_duration"] = round(duration, 2)
            
            # Salvar relatório detalhado
            integration_file = self.reports_dir / "integration_report.json"
            with open(integration_file, "w", encoding="utf-8") as f:
                json.dump(integration_report, f, indent=2, ensure_ascii=False)
            
            success_rate = integration_report["summary"]["success_rate"]
            self.log(f"✅ Testes de integração concluídos - Taxa de sucesso: {success_rate}%")
            
            return integration_report["summary"]["failed"] == 0
            
        except Exception as e:
            self.log(f"💥 Erro nos testes de integração: {e}", "ERROR")
            self.results["integration_tests"] = {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            return False
    
    def run_performance_tests(self) -> bool:
        """Executa testes de performance."""
        self.log("⚡ Executando testes de performance...")
        
        try:
            start_time = time.time()
            performance_report = self.performance_tester.run_all_benchmarks()
            duration = time.time() - start_time
            
            self.results["performance_tests"] = performance_report
            self.results["performance_tests"]["execution_duration"] = round(duration, 2)
            
            # Salvar relatório detalhado
            performance_file = self.reports_dir / "performance_report.json"
            with open(performance_file, "w", encoding="utf-8") as f:
                json.dump(performance_report, f, indent=2, ensure_ascii=False)
            
            success_rate = performance_report["summary"]["success_rate"]
            self.log(f"✅ Testes de performance concluídos - Taxa de sucesso: {success_rate}%")
            
            return performance_report["summary"]["failed"] == 0
            
        except Exception as e:
            self.log(f"💥 Erro nos testes de performance: {e}", "ERROR")
            self.results["performance_tests"] = {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            return False
    
    def generate_final_report(self):
        """Gera relatório final consolidado."""
        self.log("📊 Gerando relatório final...")
        
        # Calcular estatísticas gerais
        total_tests = 0
        total_successful = 0
        total_failed = 0
        
        if "integration_tests" in self.results and "summary" in self.results["integration_tests"]:
            int_summary = self.results["integration_tests"]["summary"]
            total_tests += int_summary.get("total_tests", 0)
            total_successful += int_summary.get("successful", 0)
            total_failed += int_summary.get("failed", 0)
        
        if "performance_tests" in self.results and "summary" in self.results["performance_tests"]:
            perf_summary = self.results["performance_tests"]["summary"]
            total_tests += perf_summary.get("total_tests", 0)
            total_successful += perf_summary.get("successful", 0)
            total_failed += perf_summary.get("failed", 0)
        
        overall_success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        
        # Resumo final
        self.results["summary"] = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_success": total_failed == 0,
            "total_tests": total_tests,
            "successful_tests": total_successful,
            "failed_tests": total_failed,
            "success_rate": round(overall_success_rate, 2),
            "installation_ok": self.results.get("installation", {}).get("success", False),
            "server_startup_ok": self.results.get("server_startup", {}).get("success", False),
            "integration_tests_ok": self.results.get("integration_tests", {}).get("summary", {}).get("failed", 1) == 0,
            "performance_tests_ok": self.results.get("performance_tests", {}).get("summary", {}).get("failed", 1) == 0
        }
        
        # Salvar relatório final
        final_report_file = self.reports_dir / "final_summary.json"
        with open(final_report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.log(f"📋 Relatório final salvo em: {final_report_file}")
        
        # Gerar relatório HTML
        self.generate_html_report()
    
    def generate_html_report(self):
        """Gera relatório HTML."""
        try:
            html_content = self._create_html_report()
            html_file = self.reports_dir / "final_summary.html"
            
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            self.log(f"🌐 Relatório HTML salvo em: {html_file}")
            
        except Exception as e:
            self.log(f"Erro ao gerar relatório HTML: {e}", "ERROR")
    
    def _create_html_report(self) -> str:
        """Cria conteúdo HTML do relatório."""
        summary = self.results.get("summary", {})
        
        status_icon = "✅" if summary.get("overall_success", False) else "❌"
        status_class = "success" if summary.get("overall_success", False) else "failure"
        
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Final - Testes PDF Preprocessor</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .status.success {{ color: #28a745; }}
        .status.failure {{ color: #dc3545; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #495057; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .success-cell {{ color: #28a745; }}
        .failure-cell {{ color: #dc3545; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{status_icon} Relatório Final de Testes</h1>
            <h2>Sistema de Pré-processamento de PDF com Descrição de Imagens</h2>
            <p class="timestamp">Gerado em: {summary.get('timestamp', 'N/A')}</p>
            <p class="status {status_class}">Status Geral: {'SUCESSO' if summary.get('overall_success', False) else 'FALHA'}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total de Testes</h3>
                <div class="value">{summary.get('total_tests', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Sucessos</h3>
                <div class="value success-cell">{summary.get('successful_tests', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Falhas</h3>
                <div class="value failure-cell">{summary.get('failed_tests', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Taxa de Sucesso</h3>
                <div class="value">{summary.get('success_rate', 0)}%</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Status dos Componentes</h2>
            <table>
                <tr>
                    <th>Componente</th>
                    <th>Status</th>
                    <th>Detalhes</th>
                </tr>
                <tr>
                    <td>Instalação</td>
                    <td class="{'success-cell' if summary.get('installation_ok', False) else 'failure-cell'}">
                        {'✅ OK' if summary.get('installation_ok', False) else '❌ FALHA'}
                    </td>
                    <td>Verificação de dependências e ambiente</td>
                </tr>
                <tr>
                    <td>Servidor</td>
                    <td class="{'success-cell' if summary.get('server_startup_ok', False) else 'failure-cell'}">
                        {'✅ OK' if summary.get('server_startup_ok', False) else '❌ FALHA'}
                    </td>
                    <td>Inicialização do servidor de teste</td>
                </tr>
                <tr>
                    <td>Testes de Integração</td>
                    <td class="{'success-cell' if summary.get('integration_tests_ok', False) else 'failure-cell'}">
                        {'✅ OK' if summary.get('integration_tests_ok', False) else '❌ FALHA'}
                    </td>
                    <td>Funcionalidades principais do sistema</td>
                </tr>
                <tr>
                    <td>Testes de Performance</td>
                    <td class="{'success-cell' if summary.get('performance_tests_ok', False) else 'failure-cell'}">
                        {'✅ OK' if summary.get('performance_tests_ok', False) else '❌ FALHA'}
                    </td>
                    <td>Benchmarks e testes de carga</td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Arquivos de Relatório</h2>
            <ul>
                <li><strong>integration_report.json</strong> - Relatório detalhado dos testes de integração</li>
                <li><strong>performance_report.json</strong> - Relatório detalhado dos testes de performance</li>
                <li><strong>final_summary.json</strong> - Dados completos em formato JSON</li>
                <li><strong>performance_charts.png</strong> - Gráficos de performance (se gerados)</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Logs</h2>
            <ul>
                <li><strong>execution_pipeline.log</strong> - Log da execução da pipeline</li>
                <li><strong>test_server.log</strong> - Log do servidor de teste</li>
                <li><strong>installation.log</strong> - Log da instalação</li>
            </ul>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def cleanup(self):
        """Limpeza final."""
        self.log("🧹 Executando limpeza...")
        
        try:
            # Parar servidor
            self.server_manager.stop_server()
            self.log("✅ Servidor parado")
            
        except Exception as e:
            self.log(f"Erro na limpeza: {e}", "ERROR")
    
    def run_full_pipeline(self, integration_only: bool = False, performance_only: bool = False) -> bool:
        """Executa pipeline completa de testes."""
        self.log("🚀 Iniciando Pipeline de Testes Finais")
        start_time = time.time()
        
        try:
            # 1. Verificar instalação
            if not self.check_installation():
                return False
            
            # 2. Verificar ambiente
            self.check_environment()  # Não bloqueia execução
            
            # 3. Iniciar servidor
            if not self.start_test_server():
                return False
            
            # 4. Executar testes
            integration_success = True
            performance_success = True
            
            if not performance_only:
                integration_success = self.run_integration_tests()
            
            if not integration_only:
                performance_success = self.run_performance_tests()
            
            # 5. Gerar relatório final
            self.generate_final_report()
            
            # 6. Resultado final
            overall_success = integration_success and performance_success
            total_duration = time.time() - start_time
            
            if overall_success:
                self.log(f"🎉 Pipeline concluída com SUCESSO em {total_duration:.2f}s")
            else:
                self.log(f"❌ Pipeline concluída com FALHAS em {total_duration:.2f}s")
            
            return overall_success
            
        except KeyboardInterrupt:
            self.log("⏹️ Pipeline interrompida pelo usuário", "WARNING")
            return False
        except Exception as e:
            self.log(f"💥 Erro inesperado na pipeline: {e}", "ERROR")
            return False
        finally:
            self.cleanup()

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Pipeline de Testes Finais - PDF Preprocessor")
    parser.add_argument("--integration-only", action="store_true", help="Executar apenas testes de integração")
    parser.add_argument("--performance-only", action="store_true", help="Executar apenas testes de performance")
    parser.add_argument("--file", type=str, help="Testar arquivo específico (não implementado)")
    
    args = parser.parse_args()
    
    pipeline = TestExecutionPipeline()
    
    try:
        success = pipeline.run_full_pipeline(
            integration_only=args.integration_only,
            performance_only=args.performance_only
        )
        sys.exit(0 if success else 1)
        
    except Exception as e:
        pipeline.log(f"💥 Erro fatal: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
