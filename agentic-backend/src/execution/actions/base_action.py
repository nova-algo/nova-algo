# from abc import ABC, abstractmethod
# from typing import Dict, Any, List, Optional, TypedDict

# class ActionParameter(TypedDict):
#     name: str
#     type: str
#     description: str
#     required: bool

# class BaseAction(ABC):
#     """Base class for all executable actions in the system"""
    
#     @abstractmethod
#     def get_name(self) -> str:
#         """The unique identifier for this action"""
#         pass
    
#     @abstractmethod
#     def get_description(self) -> str:
#         """User-friendly description of what this action does"""
#         pass
    
#     @abstractmethod
#     def get_parameters(self) -> List[ActionParameter]:
#         """The parameters this action accepts"""
#         pass
    
#     @abstractmethod
#     async def execute(self, **kwargs) -> Dict[str, Any]:
#         """Execute the action with the given parameters"""
#         pass
    
#     def get_signature(self) -> str:
#         """Generate a function signature string for this action"""
#         params = self.get_parameters()
#         param_strings = []
        
#         for param in params:
#             param_str = f"{param['name']}: {param['type']}"
#             if not param.get('required', True):
#                 param_str += " = None"
#             param_strings.append(param_str)
            
#         return f"{self.get_name()}({', '.join(param_strings)})"