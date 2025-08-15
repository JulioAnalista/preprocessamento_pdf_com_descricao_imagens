#!/usr/bin/env python3
"""
Pipeline de Instalação Automatizada
Sistema de Pré-processamento de PDF com Descrição de Imagens

Este script automatiza a instalação completa do ambiente de teste.
"""

import os
import sys
import subprocess
import platform
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class InstallationPipeline:
    """Pipeline automatizada de instalação e configuração."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = Path(__file__).parent
        self.logs_dir = self.test_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.installation_log = self.logs_dir / "installation.log"
        self.requirements_file = self.test_dir / "requirements_test.txt"
        
        self.system_info = self._get_system_info()
        self.installation_steps = []
        
    def _get_system_info(self) -> Dict:
        """Coleta informações do sistema."""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "memory_gb": self._get_memory_info(),
            "disk_space_gb": self._get_disk_space()
        }
    
    def _get_memory_info(self) -> float:
        """Obtém informações de memória do sistema."""
        try:
            import psutil
            return round(psutil.virtual_memory().total / (1024**3), 2)
        except ImportError:
            return 0.0
    
    def _get_disk_space(self) -> float:
        """Obtém espaço em disco disponível."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_root)
            return round(free / (1024**3), 2)
        except:
            return 0.0
    
    def log(self, message: str, level: str = "INFO"):
        """Registra mensagem no log."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        with open(self.installation_log, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, command: List[str], description: str) -> Tuple[bool, str]:
        """Executa comando do sistema."""
        self.log(f"Executando: {description}")
        self.log(f"Comando: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log(f"✅ Sucesso: {description}")
                return True, result.stdout
            else:
                self.log(f"❌ Erro: {description}", "ERROR")
                self.log(f"Stderr: {result.stderr}", "ERROR")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ Timeout: {description}", "ERROR")
            return False, "Timeout expired"
        except Exception as e:
            self.log(f"💥 Exceção: {description} - {str(e)}", "ERROR")
            return False, str(e)
    
    def check_python_version(self) -> bool:
        """Verifica versão do Python."""
        self.log("Verificando versão do Python...")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.log(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
            return True
        else:
            self.log(f"❌ Python {version.major}.{version.minor}.{version.micro} - Versão insuficiente (requer 3.8+)", "ERROR")
            return False
    
    def create_requirements_file(self):
        """Cria arquivo de requirements para testes."""
        requirements = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "python-multipart>=0.0.6",
            "pdfplumber>=0.10.0",
            "python-slugify>=8.0.0",
            "openai>=1.0.0",
            "PyMuPDF>=1.23.0",
            "requests>=2.31.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-html>=4.1.0",
            "pytest-cov>=4.1.0",
            "psutil>=5.9.0",
            "memory-profiler>=0.61.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "Pillow>=10.0.0",
            "aiofiles>=23.0.0",
            "httpx>=0.25.0"
        ]
        
        with open(self.requirements_file, "w", encoding="utf-8") as f:
            f.write("\n".join(requirements))
        
        self.log(f"✅ Arquivo requirements criado: {self.requirements_file}")
    
    def install_dependencies(self) -> bool:
        """Instala dependências Python."""
        self.log("Instalando dependências Python...")
        
        # Atualizar pip
        success, _ = self.run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            "Atualizando pip"
        )
        
        if not success:
            self.log("⚠️ Falha ao atualizar pip, continuando...", "WARNING")
        
        # Instalar dependências
        success, output = self.run_command(
            [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)],
            "Instalando dependências do requirements_test.txt"
        )
        
        return success
    
    def verify_installation(self) -> Dict[str, bool]:
        """Verifica se as dependências foram instaladas corretamente."""
        self.log("Verificando instalação das dependências...")
        
        critical_packages = [
            "fastapi", "uvicorn", "pdfplumber", "openai", 
            "fitz", "requests", "pytest", "psutil"
        ]
        
        results = {}
        for package in critical_packages:
            try:
                __import__(package)
                results[package] = True
                self.log(f"✅ {package} - OK")
            except ImportError:
                results[package] = False
                self.log(f"❌ {package} - FALHA", "ERROR")
        
        return results
    
    def setup_test_environment(self):
        """Configura ambiente de teste."""
        self.log("Configurando ambiente de teste...")
        
        # Criar diretórios necessários
        directories = [
            self.test_dir / "test_reports",
            self.test_dir / "performance_metrics",
            self.test_dir / "error_analysis",
            self.test_dir / "temp_files",
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            self.log(f"📁 Diretório criado: {directory}")
    
    def check_environment_variables(self) -> Dict[str, bool]:
        """Verifica variáveis de ambiente necessárias."""
        self.log("Verificando variáveis de ambiente...")
        
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_CHAT_MODEL"
        ]
        
        results = {}
        for var in required_vars:
            value = os.getenv(var)
            if value:
                results[var] = True
                self.log(f"✅ {var} - Configurada")
            else:
                results[var] = False
                self.log(f"⚠️ {var} - Não configurada", "WARNING")
        
        return results
    
    def generate_installation_report(self, package_results: Dict[str, bool], env_results: Dict[str, bool]):
        """Gera relatório de instalação."""
        report_file = self.test_dir / "installation_report.json"
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self.system_info,
            "installation_steps": self.installation_steps,
            "package_verification": package_results,
            "environment_variables": env_results,
            "success": all(package_results.values()),
            "warnings": len([v for v in env_results.values() if not v])
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"📊 Relatório de instalação salvo: {report_file}")
        return report
    
    def run_installation(self) -> bool:
        """Executa pipeline completa de instalação."""
        self.log("🚀 Iniciando Pipeline de Instalação")
        self.log(f"Sistema: {self.system_info['platform']}")
        self.log(f"Python: {self.system_info['python_version']}")
        
        # Verificar Python
        if not self.check_python_version():
            return False
        
        # Criar requirements
        self.create_requirements_file()
        
        # Configurar ambiente
        self.setup_test_environment()
        
        # Instalar dependências
        if not self.install_dependencies():
            self.log("❌ Falha na instalação de dependências", "ERROR")
            return False
        
        # Verificar instalação
        package_results = self.verify_installation()
        env_results = self.check_environment_variables()
        
        # Gerar relatório
        report = self.generate_installation_report(package_results, env_results)
        
        # Resultado final
        if report["success"]:
            self.log("🎉 Instalação concluída com sucesso!")
            if report["warnings"] > 0:
                self.log(f"⚠️ {report['warnings']} variáveis de ambiente não configuradas", "WARNING")
            return True
        else:
            self.log("❌ Instalação falhou", "ERROR")
            return False

def main():
    """Função principal."""
    pipeline = InstallationPipeline()
    
    try:
        success = pipeline.run_installation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        pipeline.log("⏹️ Instalação interrompida pelo usuário", "WARNING")
        sys.exit(1)
    except Exception as e:
        pipeline.log(f"💥 Erro inesperado: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
