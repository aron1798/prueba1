# modules/ocupabilidad/__init__.py

"""
Módulo de Ocupabilidad
Gestiona la visualización y análisis de ocupación de cursos
"""

from .view import OcupabilidadModule
from .logic import AnalizadorCursos
from .processor import CursoProcessor

__all__ = ['OcupabilidadModule', 'AnalizadorCursos', 'CursoProcessor']