"""Sistema de cache para o projeto Pulse.

Este módulo implementa um sistema de cache inteligente para otimizar
o desempenho do sistema de consolidação de planilhas.
"""

import os
import json
import pickle
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict

from .config import config
from .logger import get_logger
from .metrics import metrics_collector

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Entrada do cache."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou."""
        if self.ttl_seconds is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    @property
    def age_seconds(self) -> float:
        """Idade da entrada em segundos."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def touch(self) -> None:
        """Atualiza o último acesso."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "key": self.key,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "ttl_seconds": self.ttl_seconds,
            "size_bytes": self.size_bytes,
            "age_seconds": self.age_seconds,
            "is_expired": self.is_expired,
            "metadata": self.metadata
        }


class LRUCache(Generic[T]):
    """Cache LRU (Least Recently Used) thread-safe."""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # Estatísticas
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        self.logger.info(f"LRUCache inicializado", max_size=max_size, default_ttl=default_ttl)
    
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Obtém um valor do cache.
        
        Args:
            key: Chave do cache
            default: Valor padrão se não encontrado
            
        Returns:
            Valor do cache ou default
        """
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                metrics_collector.increment_counter("cache_misses")
                self.logger.debug(f"Cache miss: {key}")
                return default
            
            entry = self._cache[key]
            
            # Verifica expiração
            if entry.is_expired:
                del self._cache[key]
                self.misses += 1
                metrics_collector.increment_counter("cache_misses")
                metrics_collector.increment_counter("cache_expired")
                self.logger.debug(f"Cache expired: {key}")
                return default
            
            # Move para o final (mais recente)
            self._cache.move_to_end(key)
            entry.touch()
            
            self.hits += 1
            metrics_collector.increment_counter("cache_hits")
            self.logger.debug(f"Cache hit: {key}", access_count=entry.access_count)
            
            return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[int] = None, **metadata) -> None:
        """Define um valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Time to live em segundos
            **metadata: Metadados adicionais
        """
        with self._lock:
            now = datetime.now()
            ttl = ttl or self.default_ttl
            
            # Calcula tamanho aproximado
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                size_bytes = 0
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                ttl_seconds=ttl,
                size_bytes=size_bytes,
                metadata=metadata
            )
            
            # Remove entrada existente se houver
            if key in self._cache:
                del self._cache[key]
            
            # Adiciona nova entrada
            self._cache[key] = entry
            
            # Verifica limite de tamanho
            while len(self._cache) > self.max_size:
                self._evict_lru()
            
            metrics_collector.increment_counter("cache_sets")
            self.logger.debug(
                f"Cache set: {key}",
                ttl=ttl,
                size_bytes=size_bytes,
                **metadata
            )
    
    def delete(self, key: str) -> bool:
        """Remove uma entrada do cache.
        
        Args:
            key: Chave a remover
            
        Returns:
            True se removido, False se não encontrado
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                metrics_collector.increment_counter("cache_deletes")
                self.logger.debug(f"Cache delete: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            metrics_collector.increment_counter("cache_clears")
            self.logger.info(f"Cache cleared", entries_removed=count)
    
    def cleanup_expired(self) -> int:
        """Remove entradas expiradas.
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                metrics_collector.increment_counter("cache_expired", len(expired_keys))
                self.logger.info(f"Removed expired entries", count=len(expired_keys))
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            total_size = sum(entry.size_bytes for entry in self._cache.values())
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": hit_rate,
                "total_size_bytes": total_size,
                "avg_size_bytes": total_size / len(self._cache) if self._cache else 0
            }
    
    def get_entries_info(self) -> List[Dict[str, Any]]:
        """Retorna informações sobre as entradas."""
        with self._lock:
            return [entry.to_dict() for entry in self._cache.values()]
    
    def _evict_lru(self) -> None:
        """Remove a entrada menos recentemente usada."""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self.evictions += 1
            metrics_collector.increment_counter("cache_evictions")
            self.logger.debug(f"Cache eviction: {key}", age_seconds=entry.age_seconds)


class FileCache:
    """Cache persistente em arquivo."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_file_age_hours: int = 24):
        self.cache_dir = cache_dir or (config.PROJECT_ROOT / "cache")
        self.max_file_age_hours = max_file_age_hours
        self.logger = get_logger(self.__class__.__name__)
        
        # Cria diretório se não existir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            f"FileCache inicializado",
            cache_dir=str(self.cache_dir),
            max_file_age_hours=max_file_age_hours
        )
    
    def _get_cache_path(self, key: str) -> Path:
        """Gera caminho do arquivo de cache."""
        # Usa hash para evitar problemas com caracteres especiais
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Obtém valor do cache de arquivo.
        
        Args:
            key: Chave do cache
            default: Valor padrão
            
        Returns:
            Valor do cache ou default
        """
        cache_path = self._get_cache_path(key)
        
        try:
            if not cache_path.exists():
                metrics_collector.increment_counter("file_cache_misses")
                return default
            
            # Verifica idade do arquivo
            file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            if file_age > timedelta(hours=self.max_file_age_hours):
                cache_path.unlink()
                metrics_collector.increment_counter("file_cache_expired")
                self.logger.debug(f"File cache expired: {key}")
                return default
            
            # Carrega dados
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            metrics_collector.increment_counter("file_cache_hits")
            self.logger.debug(f"File cache hit: {key}")
            return data
            
        except Exception as e:
            self.logger.error(f"Erro ao ler cache de arquivo: {key}", error=str(e))
            metrics_collector.increment_counter("file_cache_errors")
            return default
    
    def set(self, key: str, value: T) -> bool:
        """Define valor no cache de arquivo.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            
        Returns:
            True se salvo com sucesso
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            
            metrics_collector.increment_counter("file_cache_sets")
            self.logger.debug(f"File cache set: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache de arquivo: {key}", error=str(e))
            metrics_collector.increment_counter("file_cache_errors")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove entrada do cache de arquivo.
        
        Args:
            key: Chave a remover
            
        Returns:
            True se removido
        """
        cache_path = self._get_cache_path(key)
        
        try:
            if cache_path.exists():
                cache_path.unlink()
                metrics_collector.increment_counter("file_cache_deletes")
                self.logger.debug(f"File cache delete: {key}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao deletar cache de arquivo: {key}", error=str(e))
            return False
    
    def cleanup_old_files(self) -> int:
        """Remove arquivos de cache antigos.
        
        Returns:
            Número de arquivos removidos
        """
        removed_count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.max_file_age_hours)
        
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_time < cutoff_time:
                    cache_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                metrics_collector.increment_counter("file_cache_cleanup", removed_count)
                self.logger.info(f"File cache cleanup", files_removed=removed_count)
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza do cache de arquivo", error=str(e))
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache de arquivo."""
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "files_count": len(cache_files),
                "total_size_bytes": total_size,
                "cache_dir": str(self.cache_dir),
                "max_file_age_hours": self.max_file_age_hours
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas do cache de arquivo", error=str(e))
            return {}


class CacheManager:
    """Gerenciador principal de cache."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # Caches especializados
        self.memory_cache = LRUCache[Any](max_size=config.CACHE_MAX_SIZE, default_ttl=config.CACHE_TTL)
        self.file_cache = FileCache(max_file_age_hours=24)
        
        # Cache para metadados de arquivos
        self.file_metadata_cache = LRUCache[Dict](max_size=500, default_ttl=300)  # 5 minutos
        
        # Cache para dados de planilhas
        self.spreadsheet_cache = LRUCache[Any](max_size=100, default_ttl=1800)  # 30 minutos
        
        self.logger.info("CacheManager inicializado")
    
    def get_file_hash(self, file_path: Path) -> Optional[str]:
        """Calcula hash de um arquivo para cache.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Hash MD5 do arquivo ou None se erro
        """
        try:
            if not file_path.exists():
                return None
            
            # Usa metadados do arquivo para hash rápido
            stat = file_path.stat()
            content = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular hash do arquivo: {file_path}", error=str(e))
            return None
    
    def cache_file_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> None:
        """Armazena metadados de arquivo no cache.
        
        Args:
            file_path: Caminho do arquivo
            metadata: Metadados a armazenar
        """
        key = str(file_path)
        file_hash = self.get_file_hash(file_path)
        
        if file_hash:
            metadata["file_hash"] = file_hash
            self.file_metadata_cache.set(key, metadata, file_path=str(file_path))
    
    def get_file_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Obtém metadados de arquivo do cache.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Metadados do cache ou None se não encontrado/inválido
        """
        key = str(file_path)
        cached_metadata = self.file_metadata_cache.get(key)
        
        if cached_metadata:
            # Verifica se o arquivo mudou
            current_hash = self.get_file_hash(file_path)
            if current_hash and cached_metadata.get("file_hash") == current_hash:
                return cached_metadata
            else:
                # Remove cache inválido
                self.file_metadata_cache.delete(key)
        
        return None
    
    def cleanup_all(self) -> Dict[str, int]:
        """Limpa todos os caches.
        
        Returns:
            Estatísticas de limpeza
        """
        stats = {
            "memory_expired": self.memory_cache.cleanup_expired(),
            "file_metadata_expired": self.file_metadata_cache.cleanup_expired(),
            "spreadsheet_expired": self.spreadsheet_cache.cleanup_expired(),
            "old_files": self.file_cache.cleanup_old_files()
        }
        
        self.logger.info("Cache cleanup completed", **stats)
        return stats
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas globais de cache."""
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "file_metadata_cache": self.file_metadata_cache.get_stats(),
            "spreadsheet_cache": self.spreadsheet_cache.get_stats(),
            "file_cache": self.file_cache.get_stats()
        }


# Instância global do gerenciador de cache
cache_manager = CacheManager()


# Decorador para cache automático
def cached(ttl: Optional[int] = None, cache_type: str = "memory", key_func: Optional[Callable] = None):
    """Decorador para cache automático de funções.
    
    Args:
        ttl: Time to live em segundos
        cache_type: Tipo de cache ('memory' ou 'file')
        key_func: Função para gerar chave do cache
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave do cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Usa nome da função e argumentos
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func.__module__}.{func.__name__}_{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Seleciona cache
            if cache_type == "file":
                cache = cache_manager.file_cache
            else:
                cache = cache_manager.memory_cache
            
            # Tenta obter do cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Executa função e armazena resultado
            result = func(*args, **kwargs)
            
            if cache_type == "file":
                cache.set(cache_key, result)
            else:
                cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# Funções de conveniência
def get_cached(key: str, default: Optional[T] = None) -> Optional[T]:
    """Função de conveniência para obter do cache de memória."""
    return cache_manager.memory_cache.get(key, default)

def set_cached(key: str, value: T, ttl: Optional[int] = None, **metadata) -> None:
    """Função de conveniência para definir no cache de memória."""
    cache_manager.memory_cache.set(key, value, ttl, **metadata)

def clear_cache() -> None:
    """Função de conveniência para limpar cache de memória."""
    cache_manager.memory_cache.clear()

def cleanup_cache() -> Dict[str, int]:
    """Função de conveniência para limpeza de cache."""
    return cache_manager.cleanup_all()

def get_cache_stats() -> Dict[str, Any]:
    """Função de conveniência para estatísticas de cache."""
    return cache_manager.get_global_stats()