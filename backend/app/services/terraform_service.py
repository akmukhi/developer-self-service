"""
Terraform execution service
Handles running Terraform commands and managing infrastructure as code
"""

import logging
import subprocess
import json
import os
import tempfile
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class TerraformService:
    """Service for executing Terraform commands"""

    def __init__(self, terraform_binary: str = "terraform", workspace_base: Optional[str] = None):
        """
        Initialize Terraform service
        
        Args:
            terraform_binary: Path to terraform binary (default: 'terraform' in PATH)
            workspace_base: Base directory for Terraform workspaces (default: temp directory)
        """
        self.terraform_binary = terraform_binary
        self.workspace_base = workspace_base or os.path.join(tempfile.gettempdir(), "terraform-workspaces")
        os.makedirs(self.workspace_base, exist_ok=True)
        self._verify_terraform()

    def _verify_terraform(self):
        """Verify Terraform is installed and accessible"""
        try:
            result = self._run_command(["version"], capture_output=True, check=True)
            version_output = result.stdout.decode() if result.stdout else ""
            logger.info(f"Terraform version: {version_output.split()[1] if len(version_output.split()) > 1 else 'unknown'}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Terraform not found or not accessible: {e}")
            raise Exception("Terraform is not installed or not in PATH")

    def _run_command(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        capture_output: bool = True,
        check: bool = False,
        timeout: Optional[int] = 300
    ) -> subprocess.CompletedProcess:
        """
        Run a Terraform command
        
        Args:
            args: Command arguments (without 'terraform' prefix)
            cwd: Working directory
            capture_output: Capture stdout/stderr
            check: Raise exception on non-zero exit
            timeout: Command timeout in seconds
        """
        cmd = [self.terraform_binary] + args
        logger.debug(f"Running command: {' '.join(cmd)} in {cwd or os.getcwd()}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                check=check,
                timeout=timeout,
                text=True
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Terraform command timed out: {' '.join(cmd)}")
            raise Exception(f"Terraform command timed out after {timeout} seconds")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Terraform command failed: {error_msg}")
            raise Exception(f"Terraform command failed: {error_msg}")
        except FileNotFoundError:
            raise Exception(f"Terraform binary not found: {self.terraform_binary}")

    def create_workspace(self, workspace_id: str) -> str:
        """
        Create a new Terraform workspace directory
        
        Args:
            workspace_id: Unique workspace identifier
            
        Returns:
            Path to the workspace directory
        """
        workspace_path = os.path.join(self.workspace_base, workspace_id)
        os.makedirs(workspace_path, exist_ok=True)
        logger.info(f"Created Terraform workspace: {workspace_path}")
        return workspace_path

    def initialize_workspace(
        self,
        workspace_path: str,
        module_path: Optional[str] = None,
        backend_config: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a Terraform workspace
        
        Args:
            workspace_path: Path to workspace directory
            module_path: Path to Terraform module (if using modules)
            backend_config: Backend configuration (for remote state)
        """
        try:
            # Copy module files to workspace if module_path is provided
            if module_path and os.path.exists(module_path):
                for item in os.listdir(module_path):
                    src = os.path.join(module_path, item)
                    dst = os.path.join(workspace_path, item)
                    if os.path.isfile(src) and not item.startswith('.'):
                        shutil.copy2(src, dst)
                    elif os.path.isdir(src) and item != '.terraform':
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)

            # Run terraform init
            init_args = ["init"]
            if backend_config:
                for key, value in backend_config.items():
                    init_args.extend(["-backend-config", f"{key}={value}"])

            result = self._run_command(init_args, cwd=workspace_path, check=True)
            
            return {
                "success": True,
                "workspace_path": workspace_path,
                "output": result.stdout if result.stdout else ""
            }
        except Exception as e:
            logger.error(f"Failed to initialize workspace: {e}")
            return {
                "success": False,
                "workspace_path": workspace_path,
                "error": str(e)
            }

    def plan(
        self,
        workspace_path: str,
        variables: Optional[Dict[str, Any]] = None,
        destroy: bool = False
    ) -> Dict[str, Any]:
        """
        Run terraform plan
        
        Args:
            workspace_path: Path to workspace directory
            variables: Terraform variables
            destroy: Whether this is a destroy plan
            
        Returns:
            Plan result with changes summary
        """
        try:
            plan_file = os.path.join(workspace_path, "tfplan")
            plan_args = ["plan", "-out", plan_file]
            
            if destroy:
                plan_args.append("-destroy")
            
            # Add variables
            if variables:
                for key, value in variables.items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    plan_args.extend(["-var", f"{key}={value}"])

            result = self._run_command(plan_args, cwd=workspace_path, check=False)
            
            # Parse plan output
            plan_output = result.stdout if result.stdout else ""
            changes = self._parse_plan_output(plan_output)
            
            return {
                "success": result.returncode == 0,
                "plan_file": plan_file,
                "output": plan_output,
                "changes": changes,
                "will_destroy": destroy
            }
        except Exception as e:
            logger.error(f"Failed to run terraform plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def apply(
        self,
        workspace_path: str,
        plan_file: Optional[str] = None,
        auto_approve: bool = True
    ) -> Dict[str, Any]:
        """
        Run terraform apply
        
        Args:
            workspace_path: Path to workspace directory
            plan_file: Path to plan file (from terraform plan)
            auto_approve: Automatically approve the apply
            
        Returns:
            Apply result with outputs
        """
        try:
            apply_args = ["apply"]
            
            if plan_file and os.path.exists(plan_file):
                apply_args.append(plan_file)
            
            if auto_approve:
                apply_args.append("-auto-approve")

            result = self._run_command(apply_args, cwd=workspace_path, check=True)
            
            # Get outputs
            outputs = self.get_outputs(workspace_path)
            
            return {
                "success": True,
                "output": result.stdout if result.stdout else "",
                "outputs": outputs
            }
        except Exception as e:
            logger.error(f"Failed to run terraform apply: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def destroy(
        self,
        workspace_path: str,
        variables: Optional[Dict[str, Any]] = None,
        auto_approve: bool = True
    ) -> Dict[str, Any]:
        """
        Run terraform destroy
        
        Args:
            workspace_path: Path to workspace directory
            variables: Terraform variables
            auto_approve: Automatically approve the destroy
            
        Returns:
            Destroy result
        """
        try:
            destroy_args = ["destroy"]
            
            if auto_approve:
                destroy_args.append("-auto-approve")
            
            # Add variables
            if variables:
                for key, value in variables.items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    destroy_args.extend(["-var", f"{key}={value}"])

            result = self._run_command(destroy_args, cwd=workspace_path, check=True)
            
            return {
                "success": True,
                "output": result.stdout if result.stdout else ""
            }
        except Exception as e:
            logger.error(f"Failed to run terraform destroy: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_outputs(self, workspace_path: str) -> Dict[str, Any]:
        """
        Get Terraform outputs
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Dictionary of output values
        """
        try:
            result = self._run_command(["output", "-json"], cwd=workspace_path, check=True)
            outputs_json = json.loads(result.stdout) if result.stdout else {}
            
            # Extract values from output structure
            outputs = {}
            for key, value_obj in outputs_json.items():
                if isinstance(value_obj, dict) and "value" in value_obj:
                    outputs[key] = value_obj["value"]
                else:
                    outputs[key] = value_obj
            
            return outputs
        except Exception as e:
            logger.warning(f"Failed to get Terraform outputs: {e}")
            return {}

    def get_state(self, workspace_path: str) -> Dict[str, Any]:
        """
        Get Terraform state
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            State dictionary
        """
        try:
            result = self._run_command(["show", "-json"], cwd=workspace_path, check=True)
            state = json.loads(result.stdout) if result.stdout else {}
            return state
        except Exception as e:
            logger.warning(f"Failed to get Terraform state: {e}")
            return {}

    def _parse_plan_output(self, output: str) -> Dict[str, Any]:
        """
        Parse terraform plan output to extract change summary
        
        Args:
            output: Terraform plan output text
            
        Returns:
            Dictionary with change counts
        """
        changes = {
            "add": 0,
            "change": 0,
            "destroy": 0
        }
        
        lines = output.split("\n")
        for line in lines:
            if "Plan:" in line:
                # Try to extract numbers from lines like:
                # Plan: 2 to add, 0 to change, 1 to destroy
                import re
                add_match = re.search(r'(\d+)\s+to\s+add', line)
                change_match = re.search(r'(\d+)\s+to\s+change', line)
                destroy_match = re.search(r'(\d+)\s+to\s+destroy', line)
                
                if add_match:
                    changes["add"] = int(add_match.group(1))
                if change_match:
                    changes["change"] = int(change_match.group(1))
                if destroy_match:
                    changes["destroy"] = int(destroy_match.group(1))
                break
        
        return changes

    def cleanup_workspace(self, workspace_path: str):
        """
        Clean up a workspace directory
        
        Args:
            workspace_path: Path to workspace directory
        """
        try:
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
                logger.info(f"Cleaned up workspace: {workspace_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup workspace {workspace_path}: {e}")

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        """
        Run terraform validate
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Validation result
        """
        try:
            result = self._run_command(["validate"], cwd=workspace_path, check=False)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout if result.stdout else "",
                "error": result.stderr if result.stderr else ""
            }
        except Exception as e:
            logger.error(f"Failed to validate Terraform: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def format_check(self, workspace_path: str) -> Dict[str, Any]:
        """
        Check Terraform formatting
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Format check result
        """
        try:
            result = self._run_command(["fmt", "-check"], cwd=workspace_path, check=False)
            
            return {
                "formatted": result.returncode == 0,
                "output": result.stdout if result.stdout else ""
            }
        except Exception as e:
            logger.error(f"Failed to check Terraform format: {e}")
            return {
                "formatted": False,
                "error": str(e)
            }


# Singleton instance
_terraform_service: Optional[TerraformService] = None


def get_terraform_service(terraform_binary: str = "terraform") -> TerraformService:
    """Get or create Terraform service instance"""
    global _terraform_service
    if _terraform_service is None:
        _terraform_service = TerraformService(terraform_binary=terraform_binary)
    return _terraform_service

