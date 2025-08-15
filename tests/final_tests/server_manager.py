#!/usr/bin/env python3
"""
Gerenciador de Servidor para Testes
Sistema de Pré-processamento de PDF com Descrição de Imagens

Este módulo gerencia o servidor de teste para execução dos testes de integração.
"""

import os
import sys
import time
import signal
import subprocess
import requests
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import queue

class ServerManager:
    """Gerenciador do servidor de teste."""
    
    def __init__(self, port: int = 8099, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.base_url = f"http://{host}:{port}"
        
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = Path(__file__).parent
        self.logs_dir = self.test_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.server_process: Optional[subprocess.Popen] = None
        self.server_log_file = self.logs_dir / "test_server.log"
        self.is_running = False
        
        # Queue para comunicação entre threads
        self.log_queue = queue.Queue()
        self.log_thread: Optional[threading.Thread] = None
        
    def log(self, message: str, level: str = "INFO"):
        """Registra mensagem no log."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [SERVER] [{level}] {message}"
        print(log_entry)
        
        with open(self.server_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def check_port_available(self) -> bool:
        """Verifica se a porta está disponível."""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((self.host, self.port))
                return result != 0
        except Exception as e:
            self.log(f"Erro ao verificar porta: {e}", "ERROR")
            return False
    
    def kill_existing_server(self):
        """Mata processos existentes na porta."""
        self.log(f"Verificando processos na porta {self.port}...")
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.info['connections']
                    if connections:
                        for conn in connections:
                            if conn.laddr.port == self.port:
                                self.log(f"Matando processo {proc.info['pid']} ({proc.info['name']})")
                                proc.kill()
                                time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.log(f"Erro ao matar processos existentes: {e}", "WARNING")
    
    def start_server(self, timeout: int = 30) -> bool:
        """Inicia o servidor de teste."""
        self.log("Iniciando servidor de teste...")
        
        # Verificar se a porta está disponível
        if not self.check_port_available():
            self.log(f"Porta {self.port} em uso, tentando matar processos existentes...")
            self.kill_existing_server()
            time.sleep(2)
            
            if not self.check_port_available():
                self.log(f"Não foi possível liberar a porta {self.port}", "ERROR")
                return False
        
        # Comando para iniciar o servidor
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", "info"
        ]
        
        try:
            # Iniciar processo do servidor
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Iniciar thread para capturar logs
            self.log_thread = threading.Thread(
                target=self._capture_server_logs,
                daemon=True
            )
            self.log_thread.start()
            
            # Aguardar servidor ficar disponível
            self.log(f"Aguardando servidor ficar disponível em {self.base_url}...")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self._check_server_health():
                    self.is_running = True
                    self.log("✅ Servidor iniciado com sucesso!")
                    return True
                
                time.sleep(1)
            
            self.log("❌ Timeout ao aguardar servidor", "ERROR")
            self.stop_server()
            return False
            
        except Exception as e:
            self.log(f"Erro ao iniciar servidor: {e}", "ERROR")
            return False
    
    def _capture_server_logs(self):
        """Captura logs do servidor em thread separada."""
        if not self.server_process or not self.server_process.stdout:
            return
        
        try:
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"[{timestamp}] [UVICORN] {line.strip()}"
                    
                    with open(self.server_log_file, "a", encoding="utf-8") as f:
                        f.write(log_entry + "\n")
                
                if self.server_process.poll() is not None:
                    break
        except Exception as e:
            self.log(f"Erro ao capturar logs do servidor: {e}", "ERROR")
    
    def _check_server_health(self) -> bool:
        """Verifica se o servidor está respondendo."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def stop_server(self):
        """Para o servidor de teste."""
        self.log("Parando servidor de teste...")
        
        if self.server_process:
            try:
                # Tentar parar graciosamente
                self.server_process.terminate()
                
                # Aguardar até 10 segundos
                try:
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Forçar parada
                    self.log("Forçando parada do servidor...", "WARNING")
                    self.server_process.kill()
                    self.server_process.wait()
                
                self.log("✅ Servidor parado")
                
            except Exception as e:
                self.log(f"Erro ao parar servidor: {e}", "ERROR")
            
            finally:
                self.server_process = None
                self.is_running = False
    
    def get_server_status(self) -> Dict[str, Any]:
        """Obtém status do servidor."""
        status = {
            "running": self.is_running,
            "url": self.base_url,
            "process_id": self.server_process.pid if self.server_process else None,
            "health_check": False,
            "response_time": None
        }
        
        if self.is_running:
            start_time = time.time()
            status["health_check"] = self._check_server_health()
            status["response_time"] = round((time.time() - start_time) * 1000, 2)
        
        return status
    
    def restart_server(self, timeout: int = 30) -> bool:
        """Reinicia o servidor."""
        self.log("Reiniciando servidor...")
        self.stop_server()
        time.sleep(2)
        return self.start_server(timeout)
    
    def wait_for_server(self, timeout: int = 60) -> bool:
        """Aguarda o servidor ficar disponível."""
        self.log(f"Aguardando servidor por até {timeout} segundos...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_server_health():
                return True
            time.sleep(1)
        
        return False
    
    def __enter__(self):
        """Context manager - entrada."""
        if self.start_server():
            return self
        else:
            raise RuntimeError("Falha ao iniciar servidor")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída."""
        self.stop_server()

def main():
    """Função principal para teste do gerenciador."""
    manager = ServerManager()
    
    try:
        print("Testando gerenciador de servidor...")
        
        # Testar inicialização
        if manager.start_server():
            print("✅ Servidor iniciado com sucesso")
            
            # Testar status
            status = manager.get_server_status()
            print(f"Status: {status}")
            
            # Aguardar um pouco
            time.sleep(5)
            
            # Parar servidor
            manager.stop_server()
            print("✅ Servidor parado com sucesso")
        else:
            print("❌ Falha ao iniciar servidor")
            
    except KeyboardInterrupt:
        print("\n⏹️ Interrompido pelo usuário")
        manager.stop_server()
    except Exception as e:
        print(f"💥 Erro: {e}")
        manager.stop_server()

if __name__ == "__main__":
    main()
