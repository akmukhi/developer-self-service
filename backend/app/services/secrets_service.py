"""
Secret rotation service
Handles secret generation, rotation, and management using Kubernetes Secrets API
"""

import logging
import secrets
import string
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.kubernetes_service import get_kubernetes_service
from app.models.secret import Secret, SecretRotateRequest, SecretRotationHistory, SecretType

logger = logging.getLogger(__name__)


class SecretsService:
    """Service for managing and rotating secrets"""

    def __init__(self):
        """Initialize secrets service"""
        self.kubernetes = get_kubernetes_service()

    def generate_secret_value(self, length: int = 32, include_special: bool = True) -> str:
        """
        Generate a secure random secret value
        
        Args:
            length: Length of the secret
            include_special: Include special characters
            
        Returns:
            Generated secret string
        """
        alphabet = string.ascii_letters + string.digits
        if include_special:
            alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def generate_secret_key(self, length: int = 16) -> str:
        """Generate a random secret key (alphanumeric only, URL-safe)"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_secret(
        self,
        name: str,
        namespace: str = "default",
        secret_type: SecretType = SecretType.OPAQUE,
        keys: Optional[List[str]] = None,
        values: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Kubernetes secret
        
        Args:
            name: Secret name
            namespace: Kubernetes namespace
            secret_type: Type of secret
            keys: List of secret keys to generate
            values: Dictionary of key-value pairs (if provided, keys are ignored)
            
        Returns:
            Secret information
        """
        try:
            # Generate values if not provided
            if values is None:
                if keys is None:
                    keys = ["password", "api_key"]
                values = {key: self.generate_secret_value() for key in keys}
            
            # Create secret in Kubernetes
            secret_info = self.kubernetes.create_secret(
                name=name,
                namespace=namespace,
                data=values,
                secret_type=secret_type.value
            )
            
            logger.info(f"Created secret {name} in namespace {namespace}")
            return secret_info
        except Exception as e:
            logger.error(f"Failed to create secret: {e}")
            raise Exception(f"Failed to create secret: {str(e)}")

    def get_secret(self, name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get secret information (metadata only, not values)
        
        Args:
            name: Secret name
            namespace: Kubernetes namespace
            
        Returns:
            Secret information or None if not found
        """
        try:
            return self.kubernetes.get_secret(name=name, namespace=namespace)
        except Exception as e:
            logger.error(f"Failed to get secret: {e}")
            return None

    def rotate_secret(
        self,
        name: str,
        namespace: str = "default",
        keys: Optional[List[str]] = None,
        generate_new: bool = True,
        new_values: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Rotate a Kubernetes secret
        
        Args:
            name: Secret name
            namespace: Kubernetes namespace
            keys: Specific keys to rotate (all if None)
            generate_new: Generate new values (if False, must provide new_values)
            new_values: New secret values (if provided, generate_new is ignored)
            
        Returns:
            Rotation result with new secret info
        """
        try:
            # Get existing secret
            existing_secret = self.kubernetes.get_secret(name=name, namespace=namespace)
            if not existing_secret:
                raise Exception(f"Secret {name} not found in namespace {namespace}")
            
            existing_keys = existing_secret.get("keys", [])
            
            # Determine which keys to rotate
            keys_to_rotate = keys if keys else existing_keys
            
            # Validate keys exist
            for key in keys_to_rotate:
                if key not in existing_keys:
                    raise Exception(f"Key {key} not found in secret {name}")
            
            # Generate or use provided new values
            if new_values is None:
                if not generate_new:
                    raise Exception("Must provide new_values if generate_new is False")
                new_values = {key: self.generate_secret_value() for key in keys_to_rotate}
            else:
                # Only update specified keys
                if keys:
                    new_values = {k: v for k, v in new_values.items() if k in keys_to_rotate}
            
            # Get all existing values (we need to read the full secret to preserve non-rotated keys)
            # Since we can't read values via API, we'll update only the specified keys
            # In a real implementation, you might want to store a mapping or use a secret manager
            
            # Update secret in Kubernetes
            updated_secret = self.kubernetes.update_secret(
                name=name,
                namespace=namespace,
                data=new_values
            )
            
            logger.info(f"Rotated secret {name} in namespace {namespace}, keys: {keys_to_rotate}")
            
            return {
                "success": True,
                "secret": updated_secret,
                "rotated_keys": keys_to_rotate,
                "rotated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to rotate secret: {e}")
            raise Exception(f"Failed to rotate secret: {str(e)}")

    def rotate_service_secrets(
        self,
        service_id: str,
        secret_name: Optional[str] = None,
        namespace: str = "default",
        keys: Optional[List[str]] = None,
        update_deployments: bool = True
    ) -> Dict[str, Any]:
        """
        Rotate secrets for a service and optionally update deployments
        
        Args:
            service_id: Service identifier
            secret_name: Secret name (defaults to {service_id}-secrets)
            namespace: Kubernetes namespace
            keys: Specific keys to rotate
            update_deployments: Update deployments to use new secrets (rolling restart)
            
        Returns:
            Rotation result
        """
        try:
            if secret_name is None:
                secret_name = f"{service_id}-secrets"
            
            # Rotate the secret
            rotation_result = self.rotate_secret(
                name=secret_name,
                namespace=namespace,
                keys=keys,
                generate_new=True
            )
            
            # Update deployments if requested
            if update_deployments:
                self._update_deployments_for_secret(
                    secret_name=secret_name,
                    namespace=namespace
                )
            
            return {
                "success": True,
                "service_id": service_id,
                "secret_name": secret_name,
                "rotation": rotation_result,
                "deployments_updated": update_deployments
            }
        except Exception as e:
            logger.error(f"Failed to rotate service secrets: {e}")
            raise Exception(f"Failed to rotate service secrets: {str(e)}")

    def _update_deployments_for_secret(self, secret_name: str, namespace: str = "default"):
        """
        Trigger rolling update for deployments using a secret
        
        Args:
            secret_name: Secret name
            namespace: Kubernetes namespace
        """
        try:
            # Get all deployments in namespace
            deployments = self.kubernetes.list_deployments(namespace=namespace)
            
            # Find deployments that use this secret
            deployments_to_update = []
            for deployment in deployments:
                deployment_name = deployment.get("name")
                if deployment_name:
                    try:
                        # Check if deployment uses this secret
                        # We'll use a simple heuristic: if deployment name matches service pattern
                        # In production, you'd query the deployment spec to check for secret references
                        # For MVP, we'll update all deployments in the namespace
                        # A better approach would be to store service-secret mappings
                        
                        # For now, trigger rolling update for all deployments
                        # In a real implementation, you'd check the deployment spec:
                        # - Check envFrom for secretRef
                        # - Check env for valueFrom.secretKeyRef
                        # - Check volumeMounts for secret volumes
                        
                        self.kubernetes.trigger_rolling_update(
                            name=deployment_name,
                            namespace=namespace
                        )
                        
                        deployments_to_update.append(deployment_name)
                        logger.info(f"Triggered rolling update for deployment {deployment_name}")
                    except Exception as e:
                        logger.warning(f"Failed to update deployment {deployment_name}: {e}")
            
            if not deployments_to_update:
                logger.info(f"No deployments found in namespace {namespace}")
            
        except Exception as e:
            logger.error(f"Failed to update deployments for secret: {e}")
            # Don't raise - secret rotation succeeded even if deployment update failed
            # In production, you might want to track this and retry

    def get_secret_rotation_history(
        self,
        name: str,
        namespace: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Get rotation history for a secret
        
        Note: In a real implementation, this would be stored in a database or
        as annotations on the secret. For MVP, we'll return basic info.
        
        Args:
            name: Secret name
            namespace: Kubernetes namespace
            
        Returns:
            List of rotation history entries
        """
        try:
            secret_info = self.kubernetes.get_secret(name=name, namespace=namespace)
            if not secret_info:
                return []
            
            # In a real implementation, you'd query a database or read annotations
            # For MVP, we'll return creation time as a single history entry
            history = []
            if secret_info.get("created_at"):
                history.append({
                    "rotated_at": secret_info["created_at"],
                    "rotated_by": "system",
                    "version": "v1"
                })
            
            return history
        except Exception as e:
            logger.error(f"Failed to get rotation history: {e}")
            return []

    def list_secrets(self, namespace: str = "default", label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List secrets in a namespace
        
        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering
            
        Returns:
            List of secret information
        """
        try:
            return self.kubernetes.list_secrets(namespace=namespace, label_selector=label_selector)
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []

    def delete_secret(self, name: str, namespace: str = "default") -> bool:
        """
        Delete a secret
        
        Args:
            name: Secret name
            namespace: Kubernetes namespace
            
        Returns:
            True if deleted, False if not found
        """
        try:
            return self.kubernetes.delete_secret(name=name, namespace=namespace)
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            raise Exception(f"Failed to delete secret: {str(e)}")

    def create_secret_for_service(
        self,
        service_id: str,
        namespace: str = "default",
        keys: Optional[List[str]] = None,
        secret_type: SecretType = SecretType.OPAQUE
    ) -> Dict[str, Any]:
        """
        Create a secret for a service with default keys
        
        Args:
            service_id: Service identifier
            namespace: Kubernetes namespace
            keys: Secret keys to create (defaults to common keys)
            secret_type: Type of secret
            
        Returns:
            Created secret information
        """
        if keys is None:
            keys = ["database_url", "api_key", "secret_key"]
        
        secret_name = f"{service_id}-secrets"
        
        return self.create_secret(
            name=secret_name,
            namespace=namespace,
            secret_type=secret_type,
            keys=keys
        )


# Singleton instance
_secrets_service: Optional[SecretsService] = None


def get_secrets_service() -> SecretsService:
    """Get or create secrets service instance"""
    global _secrets_service
    if _secrets_service is None:
        _secrets_service = SecretsService()
    return _secrets_service

