#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        🚀 Open-WA CRM Dev Manager                             ║
║                                                                               ║
║  Backend: Docker | Frontend: Local (Node.js con NVM)                          ║
║  Uso: python dev_manager.py                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import os
import sys
import signal
import shutil
from pathlib import Path

REQUIRED_NODE_VERSION = 22
SCRIPT_DIR = Path(__file__).parent.resolve()
FRONTEND_DIR = SCRIPT_DIR / 'frontend'
BACKEND_DIR = SCRIPT_DIR / 'backend'


class Colors:
    """Códigos ANSI para colores en terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    print(f"""
{Colors.CYAN}{Colors.BOLD}
   ___                    __        ___     ____ ____  __  __ 
  / _ \ _ __   ___ _ __   \ \      / / \   / ___|  _ \|  \/  |
 | | | | '_ \ / _ \ '_ \   \ \ /\ / / _ \ | |   | |_) | |\/| |
 | |_| | |_) |  __/ | | |   \ V  V / ___ \| |___|  _ <| |  | |
  \___/| .__/ \___|_| |_|    \_/\_/_/   \_\\____|_| \_\_|  |_|
       |_|                                                    
{Colors.ENDC}
{Colors.GREEN}              ⚡ Development Manager{Colors.ENDC}
""")


def print_step(msg: str):
    print(f"{Colors.BLUE}[OpenWA-Manager] ➤ {msg}{Colors.ENDC}")


def print_success(msg: str):
    print(f"{Colors.GREEN}✔ {msg}{Colors.ENDC}")


def print_error(msg: str):
    print(f"{Colors.FAIL}✖ {msg}{Colors.ENDC}")


def print_warning(msg: str):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


def check_command_exists(command: str) -> bool:
    """Verifica si un comando está disponible en el sistema"""
    return shutil.which(command) is not None


def run_command(command: str, cwd: Path = None, capture: bool = True, check: bool = True):
    """Ejecuta un comando y retorna el resultado"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd or SCRIPT_DIR,
            shell=True,
            text=True,
            capture_output=capture,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture and e.stderr:
            print_error(f"Error ejecutando: {command}")
            print(f"  {Colors.FAIL}{e.stderr.strip()}{Colors.ENDC}")
        return None


def get_nvm_command(node_cmd: str) -> str:
    """Genera un comando bash que carga NVM antes de ejecutar"""
    return f'''
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
        {node_cmd}
    '''


def check_docker_running() -> bool:
    """Verifica si Docker daemon está corriendo"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def verify_docker() -> bool:
    """Verifica que Docker esté listo"""
    print_step("Verificando Docker...")
    
    if not check_command_exists("docker"):
        print_error("Docker no está instalado.")
        print("  Instálalo desde: https://docs.docker.com/get-docker/")
        return False
    
    if not check_docker_running():
        print_error("Docker no está corriendo.")
        print("  Inicia Docker Desktop o el servicio de Docker.")
        return False
    
    print_success("Docker está listo.")
    return True


def get_node_version() -> int | None:
    """Obtiene la versión mayor de Node.js instalada"""
    try:
        result = subprocess.run(
            "node -v",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_str = result.stdout.strip().replace('v', '').split('.')[0]
            return int(version_str)
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ['bash', '-c', get_nvm_command('node -v')],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version_str = result.stdout.strip().replace('v', '').split('.')[0]
            return int(version_str)
    except Exception:
        pass
    
    return None


def check_nvm_installed() -> bool:
    """Verifica si NVM está instalado"""
    nvm_dir = Path.home() / '.nvm'
    return nvm_dir.exists() and (nvm_dir / 'nvm.sh').exists()


def install_nvm():
    """Instala NVM si no está instalado"""
    print_step("Instalando NVM (Node Version Manager)...")
    
    try:
        install_cmd = 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash'
        result = subprocess.run(
            install_cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print_success("NVM instalado correctamente.")
        return True
    except subprocess.CalledProcessError as e:
        print_error("No se pudo instalar NVM automáticamente.")
        print("  Instálalo manualmente desde: https://github.com/nvm-sh/nvm")
        return False


def install_node_with_nvm(version: int):
    """Instala y usa una versión específica de Node con NVM"""
    print_step(f"Instalando Node.js v{version} con NVM...")
    
    try:
        install_cmd = get_nvm_command(f'nvm install {version} && nvm use {version}')
        result = subprocess.run(
            ['bash', '-c', install_cmd],
            check=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        print_success(f"Node.js v{version} instalado y activado.")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error instalando Node.js: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print_error("Timeout instalando Node.js")
        return False


def setup_node_environment() -> bool:
    """Configura el entorno de Node.js completo"""
    print_step("Verificando entorno de Node.js...")
    
    current_version = get_node_version()
    
    if current_version and current_version >= REQUIRED_NODE_VERSION:
        print_success(f"Node.js v{current_version} detectado (✓ versión correcta)")
        return True
    
    if current_version:
        print_warning(f"Node.js v{current_version} detectado, pero se requiere v{REQUIRED_NODE_VERSION}+")
    else:
        print_warning("Node.js no detectado en el sistema.")
    
    if not check_nvm_installed():
        print_warning("NVM no está instalado.")
        if not install_nvm():
            return False
    else:
        print_success("NVM detectado.")
    
    if not install_node_with_nvm(REQUIRED_NODE_VERSION):
        return False
    
    return True


def run_npm_with_nvm(npm_command: str, cwd: Path, show_output: bool = False) -> bool:
    """Ejecuta un comando npm asegurándose de usar la versión correcta de Node"""
    full_command = get_nvm_command(f'nvm use {REQUIRED_NODE_VERSION} --silent && {npm_command}')
    
    try:
        if show_output:
            result = subprocess.run(
                ['bash', '-c', full_command],
                cwd=cwd,
                check=True
            )
        else:
            result = subprocess.run(
                ['bash', '-c', full_command],
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True
            )
        return True
    except subprocess.CalledProcessError as e:
        if hasattr(e, 'stderr') and e.stderr:
            print_error(e.stderr.strip())
        return False


def setup_frontend_dependencies() -> bool:
    """Instala dependencias del frontend si no existen"""
    node_modules = FRONTEND_DIR / 'node_modules'
    
    if node_modules.exists():
        print_step("Dependencias del frontend ya instaladas.")
        return True
    
    print_step("Instalando dependencias del frontend (npm install)...")
    
    if run_npm_with_nvm('npm install', FRONTEND_DIR, show_output=True):
        print_success("Dependencias instaladas correctamente.")
        return True
    else:
        print_error("Error instalando dependencias.")
        return False


def start_docker_backend():
    """Levanta el backend con Docker Compose"""
    print_step("Levantando Backend con Docker Compose...")
    print(f"{Colors.WARNING}   ⏳ Este proceso puede tardar unos minutos si es la primera vez...{Colors.ENDC}\n")
    
    compose_cmd = "docker compose" if run_command("docker compose version", check=False) else "docker-compose"
    
    try:
        result = subprocess.run(
            f"{compose_cmd} up -d --build",
            cwd=SCRIPT_DIR,
            shell=True,
            check=True
        )
        print_success("Backend corriendo en Docker.")
        return True
    except subprocess.CalledProcessError:
        print_error("Error levantando Docker Compose.")
        return False


def stop_docker_backend():
    """Detiene el backend de Docker"""
    compose_cmd = "docker compose" if run_command("docker compose version", check=False) else "docker-compose"
    run_command(f"{compose_cmd} down", cwd=SCRIPT_DIR, check=False)


def start_frontend():
    """Inicia el frontend con npm run dev usando NVM"""
    print_step("Iniciando Frontend (Vite dev server)...")
    
    full_command = get_nvm_command(f'nvm use {REQUIRED_NODE_VERSION} --silent && npm run dev')
    
    subprocess.run(
        ['bash', '-c', full_command],
        cwd=FRONTEND_DIR
    )


def shutdown(signum=None, frame=None):
    """Maneja el shutdown graceful"""
    print(f"\n\n{Colors.WARNING}🛑 Deteniendo servicios...{Colors.ENDC}")
    stop_docker_backend()
    print_success("Sistema apagado correctamente. ¡Hasta luego! 👋")
    sys.exit(0)


def start_services():
    """Flujo principal: levanta todo"""
    print_banner()
    
    if not verify_docker():
        sys.exit(1)
    
    if not setup_node_environment():
        print_error("No se pudo configurar Node.js.")
        print("  Instala Node.js v22+ manualmente o instala NVM.")
        sys.exit(1)
    
    if not setup_frontend_dependencies():
        sys.exit(1)
    
    if not start_docker_backend():
        sys.exit(1)
    
    print(f"""
{Colors.HEADER}{'═' * 60}
🚀 ¡TODO LISTO!
{'═' * 60}{Colors.ENDC}

{Colors.GREEN}👉 Frontend: http://localhost:5173{Colors.ENDC}
{Colors.GREEN}👉 Backend:  http://localhost:8000{Colors.ENDC}

{Colors.WARNING}Presiona Ctrl+C para detener todo.{Colors.ENDC}
""")
    
    try:
        start_frontend()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    start_services()
