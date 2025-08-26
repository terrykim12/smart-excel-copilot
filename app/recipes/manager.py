"""
레시피 관리 모듈 (M2)
전처리 작업을 저장하고 재실행할 수 있는 레시피 시스템을 제공합니다.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib

class Recipe:
    """전처리 레시피 클래스"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.steps = steps or []
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
    def add_step(self, step_type: str, **kwargs):
        """레시피 단계를 추가합니다."""
        step = {
            "type": step_type,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.steps.append(step)
        self.updated_at = datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """레시피를 딕셔너리로 변환합니다."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recipe':
        """딕셔너리에서 레시피를 생성합니다."""
        recipe = cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=data.get("steps", []),
            metadata=data.get("metadata", {})
        )
        recipe.created_at = data.get("created_at", recipe.created_at)
        recipe.updated_at = data.get("updated_at", recipe.updated_at)
        return recipe

class RecipeManager:
    """레시피 관리자"""
    
    def __init__(self, recipes_dir: Optional[Union[str, Path]] = None):
        if recipes_dir is None:
            # 기본 레시피 디렉토리
            recipes_dir = Path.home() / ".smart_excel_copilot" / "recipes"
        else:
            recipes_dir = Path(recipes_dir)
        
        self.recipes_dir = recipes_dir
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
        
        # 레시피 인덱스 파일
        self.index_file = self.recipes_dir / "index.json"
        self.load_index()
    
    def load_index(self):
        """레시피 인덱스를 로드합니다."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except Exception as e:
                print(f"[recipe] 인덱스 로드 오류: {e}")
                self.index = {}
        else:
            self.index = {}
    
    def save_index(self):
        """레시피 인덱스를 저장합니다."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[recipe] 인덱스 저장 오류: {e}")
    
    def save_recipe(self, recipe: Recipe, format: str = "json") -> Path:
        """레시피를 파일로 저장합니다."""
        # 파일명 생성
        safe_name = "".join(c for c in recipe.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        if format.lower() == "json":
            file_path = self.recipes_dir / f"{safe_name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recipe.to_dict(), f, ensure_ascii=False, indent=2)
        elif format.lower() == "yaml":
            file_path = self.recipes_dir / f"{safe_name}.yaml"
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(recipe.to_dict(), f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
        
        # 인덱스 업데이트
        self.index[recipe.name] = {
            "file_path": str(file_path),
            "format": format,
            "created_at": recipe.created_at,
            "updated_at": recipe.updated_at,
            "step_count": len(recipe.steps)
        }
        self.save_index()
        
        print(f"[recipe] 레시피 '{recipe.name}' 저장 완료: {file_path}")
        return file_path
    
    def load_recipe(self, name: str) -> Optional[Recipe]:
        """레시피를 로드합니다."""
        if name not in self.index:
            print(f"[recipe] 레시피 '{name}'을 찾을 수 없습니다.")
            return None
        
        file_path = Path(self.index[name]["file_path"])
        format = self.index[name]["format"]
        
        try:
            if format == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif format == "yaml":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                print(f"[recipe] 지원하지 않는 형식: {format}")
                return None
            
            return Recipe.from_dict(data)
            
        except Exception as e:
            print(f"[recipe] 레시피 로드 오류: {e}")
            return None
    
    def list_recipes(self) -> List[Dict[str, Any]]:
        """저장된 레시피 목록을 반환합니다."""
        return [
            {
                "name": name,
                **info
            }
            for name, info in self.index.items()
        ]
    
    def delete_recipe(self, name: str) -> bool:
        """레시피를 삭제합니다."""
        if name not in self.index:
            print(f"[recipe] 레시피 '{name}'을 찾을 수 없습니다.")
            return False
        
        try:
            file_path = Path(self.index[name]["file_path"])
            if file_path.exists():
                file_path.unlink()
            
            del self.index[name]
            self.save_index()
            
            print(f"[recipe] 레시피 '{name}' 삭제 완료")
            return True
            
        except Exception as e:
            print(f"[recipe] 레시피 삭제 오류: {e}")
            return False
    
    def create_recipe_from_operations(
        self,
        name: str,
        description: str,
        operations: List[Dict[str, Any]]
    ) -> Recipe:
        """작업 기록으로부터 레시피를 생성합니다."""
        recipe = Recipe(name=name, description=description)
        
        for op in operations:
            recipe.add_step(**op)
        
        return recipe
    
    def execute_recipe(
        self,
        recipe_name: str,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Optional[Path]:
        """레시피를 실행합니다."""
        recipe = self.load_recipe(recipe_name)
        if not recipe:
            return None
        
        print(f"[recipe] 레시피 '{recipe_name}' 실행 시작")
        
        # 레시피 실행 로직은 별도 구현 필요
        # 여기서는 기본적인 실행 흐름만 표시
        
        for i, step in enumerate(recipe.steps, 1):
            print(f"[recipe] 단계 {i}: {step['type']}")
            # 실제 실행 로직 구현 필요
        
        print(f"[recipe] 레시피 '{recipe_name}' 실행 완료")
        
        # 결과 파일 경로 반환
        if output_file:
            return Path(output_file)
        else:
            input_path = Path(input_file)
            return input_path.parent / f"{input_path.stem}_recipe_output{input_path.suffix}"

def create_cleaning_recipe(
    name: str,
    currency_split: bool = True,
    date_fmt: str = "YYYY-MM-DD",
    drop_empty: bool = True,
    dedupe_keys: Optional[List[str]] = None,
    keep_policy: str = "first"
) -> Recipe:
    """클리닝 레시피를 생성합니다."""
    recipe = Recipe(
        name=name,
        description=f"기본 데이터 클리닝 레시피 - 통화분리:{currency_split}, 날짜형식:{date_fmt}"
    )
    
    # 클리닝 단계 추가
    recipe.add_step(
        "clean",
        operation="level1_clean",
        currency_split=currency_split,
        date_fmt=date_fmt,
        drop_empty_rows=drop_empty,
        drop_empty_cols=drop_empty
    )
    
    # 중복 제거 단계 추가 (옵션)
    if dedupe_keys:
        recipe.add_step(
            "dedupe",
            operation="dedupe",
            keys=dedupe_keys,
            keep_policy=keep_policy
        )
    
    return recipe

def create_imputation_recipe(
    name: str,
    strategies: Dict[str, str]
) -> Recipe:
    """결측치 처리 레시피를 생성합니다."""
    recipe = Recipe(
        name=name,
        description=f"결측치 처리 레시피 - {', '.join(f'{col}:{strat}' for col, strat in strategies.items())}"
    )
    
    recipe.add_step(
        "impute",
        operation="handle_missing_values",
        strategies=strategies
    )
    
    return recipe

def create_outlier_recipe(
    name: str,
    method: str = "iqr",
    action: str = "clip",
    columns: Optional[List[str]] = None
) -> Recipe:
    """이상치 처리 레시피를 생성합니다."""
    recipe = Recipe(
        name=name,
        description=f"이상치 처리 레시피 - {method} 방법으로 {action} 처리"
    )
    
    recipe.add_step(
        "outlier",
        operation="detect_and_handle_outliers",
        method=method,
        action=action,
        columns=columns
    )
    
    return recipe
