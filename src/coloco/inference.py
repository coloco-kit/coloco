from __future__ import annotations
import ast
import inspect
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
    Type,
    Union,
    get_type_hints,
)


def _snake_case_to_capital_case(name: str) -> str:
    return "".join(word.capitalize() for word in name.split("_"))


def _sanitize_name(name: str) -> str:
    return "".join(c if c.isalnum() else "" for c in name)


def _get_module_type(func: Callable, name: str) -> Type:
    import sys

    module = sys.modules.get(func.__module__, None)
    if hasattr(module, name):
        result = getattr(module, name)
        if isinstance(result, type):
            return result
        elif isinstance(result, Callable):
            return get_return_type(result)

    return Any


def get_return_type(func: Callable) -> Type:
    """
    Infer the return type of a Python function by analyzing its AST.
    For dictionary returns, creates a TypedDict representation.

    Args:
        func: The function to analyze

    Returns:
        The inferred return type
    """

    # If annotations exist, return the return type
    if hasattr(func, "__annotations__") and "return" in func.__annotations__:
        return func.__annotations__["return"]

    # Get function source code and create AST
    try:
        source = inspect.getsource(func)
    except Exception:
        return Any

    module = ast.parse(source)

    # Extract the function definition node
    func_def = module.body[0]
    if not isinstance(func_def, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError("Input is not a function definition")

    # Create a symbol table for type analysis
    symbol_table = {}

    # Populate the symbol table with type hints from function annotations
    if func_def.returns:
        # If function has a return type annotation, use it directly
        return _resolve_annotation(func_def.returns, {}, func)

    # Gather type information from annotations and assignments
    _analyze_function_body(func_def, symbol_table, func)

    # Find all return statements
    return_types = []
    for node in ast.walk(func_def):
        if isinstance(node, ast.Return) and node.value:
            return_type = _infer_expr_type(node.value, symbol_table, func, [])
            return_types.append(return_type)

    # If we found return statements
    if return_types:
        if len(return_types) == 1:
            return return_types[0]
        else:
            # Multiple return types - use Union
            return Union[tuple(set(return_types))]

    # Default to Any if no return statements or couldn't infer
    return Any


def _analyze_function_body(
    func_def: ast.FunctionDef, symbol_table: dict[str, Type], func: Callable
) -> None:
    """Analyze function body to populate symbol table with type information"""
    # First gather parameter types
    for arg in func_def.args.args:
        if arg.annotation:
            symbol_table[arg.arg] = _resolve_annotation(arg.annotation, {}, func)

    # Analyze assignments to track variable types
    for node in ast.walk(func_def):
        if isinstance(node, ast.Assign):
            assigned_type = _infer_expr_type(node.value, symbol_table, func, [])
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbol_table[target.id] = assigned_type
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            # Handle annotated assignments
            symbol_table[node.target.id] = _resolve_annotation(
                node.annotation, {}, func
            )


def _resolve_annotation(
    annotation: ast.AST, type_context: dict[str, Any], func: Callable
) -> Type:
    """Resolve a type annotation AST node to a real type"""
    if isinstance(annotation, ast.Name):
        # Simple types like int, str, etc.
        type_name = annotation.id
        # Check Python's built-in types first
        if type_name in __builtins__:
            return __builtins__[type_name]

        # Otherwise check if it's imported
        return _get_module_type(func, type_name)

    elif isinstance(annotation, ast.Subscript):
        # Handle generic types like list[int], dict[str, int], etc.
        if isinstance(annotation.value, ast.Name):
            base_type = annotation.value.id
            if base_type == "List" or base_type == "list":
                elem_type = _resolve_annotation(annotation.slice, type_context, func)
                return list[elem_type]
            elif base_type == "Dict" or base_type == "dict":
                if isinstance(annotation.slice, ast.Tuple):
                    key_type = _resolve_annotation(
                        annotation.slice.elts[0], type_context, func
                    )
                    val_type = _resolve_annotation(
                        annotation.slice.elts[1], type_context, func
                    )
                    return dict[key_type, val_type]
                return Dict
            elif base_type == "Set" or base_type == "set":
                elem_type = _resolve_annotation(annotation.slice, type_context, func)
                return set[elem_type]
            elif base_type == "Tuple" or base_type == "tuple":
                if isinstance(annotation.slice, ast.Tuple):
                    elem_types = [
                        _resolve_annotation(e, type_context, func)
                        for e in annotation.slice.elts
                    ]
                    return tuple[tuple(elem_types)]
                return Tuple
            elif base_type == "Optional":
                elem_type = _resolve_annotation(annotation.slice, type_context, func)
                return Optional[elem_type]
            elif base_type == "Union":
                if isinstance(annotation.slice, ast.Tuple):
                    elem_types = [
                        _resolve_annotation(e, type_context, func)
                        for e in annotation.slice.elts
                    ]
                    return Union[tuple(elem_types)]
                return Union

    # Fallback for unresolved or complex annotations
    return Any


def _infer_expr_type(
    node: ast.AST, symbol_table: dict[str, Type], func: Callable, nested_path: list[str]
) -> Type:
    """Infer the type of an expression"""
    if isinstance(node, ast.Dict):
        # For dictionary literals, create a TypedDict
        return _create_typed_dict_from_dict(node, symbol_table, func, nested_path)

    elif isinstance(node, ast.List):
        # Handle list literals
        if not node.elts:
            return list[Any]
        element_types = [
            _infer_expr_type(elt, symbol_table, func, nested_path) for elt in node.elts
        ]
        if len(set(element_types)) == 1:
            return list[element_types[0]]
        return list[Union[tuple(set(element_types))]]

    elif isinstance(node, ast.Tuple):
        # Handle tuple literals
        if not node.elts:
            return tuple[()]
        element_types = [
            _infer_expr_type(elt, symbol_table, func, nested_path) for elt in node.elts
        ]
        return tuple[tuple(element_types)]

    elif isinstance(node, ast.Set):
        # Handle set literals
        if not node.elts:
            return set[Any]
        element_types = [
            _infer_expr_type(elt, symbol_table, func, nested_path) for elt in node.elts
        ]
        if len(set(element_types)) == 1:
            return set[element_types[0]]
        return set[Union[tuple(set(element_types))]]

    elif isinstance(node, ast.Constant):
        # Handle literals
        return type(node.value)

    elif isinstance(node, ast.Name):
        # Look up variable types in the symbol table
        if node.id in symbol_table:
            return symbol_table[node.id]

        # Handle built-in types referenced by name
        if node.id in __builtins__ and isinstance(__builtins__[node.id], type):
            return __builtins__[node.id]

        return _get_module_type(func, node.id)

    elif isinstance(node, ast.Call):
        # Handle function calls - this is complex, so we'll use a simplified approach
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # Handle some common built-in functions
            if func_name == "int":
                return int
            elif func_name == "str":
                return str
            elif func_name == "float":
                return float
            elif func_name == "list":
                return list[Any]
            elif func_name == "dict":
                return dict[Any, Any]
            elif func_name == "set":
                return set[Any]
            elif func_name == "tuple":
                return Tuple

            return _get_module_type(func, func_name)

        # For other function calls, we default to Any
        return Any

    elif isinstance(node, ast.BinOp):
        # Handle binary operations
        left_type = _infer_expr_type(node.left, symbol_table, func, nested_path)
        right_type = _infer_expr_type(node.right, symbol_table, func, nested_path)

        # String concatenation
        if isinstance(node.op, ast.Add) and (left_type == str or right_type == str):
            return str

        # Numeric operations typically return numeric types
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            if left_type == float or right_type == float:
                return float
            return int

        return Any

    # Default for complex or unknown expressions
    return Any


def _create_typed_dict_from_dict(
    dict_node: ast.Dict,
    symbol_table: dict[str, Type],
    func: Callable,
    nested_path: list[str],
) -> Type:
    """Create a TypedDict from a dictionary literal"""
    # Check if all keys are string literals
    field_types = {}
    is_valid_typeddict = True

    for i, key in enumerate(dict_node.keys):
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            value_type = _infer_expr_type(
                dict_node.values[i], symbol_table, func, nested_path + [key.value]
            )
            field_types[key.value] = value_type
        else:
            is_valid_typeddict = False
            break

    if is_valid_typeddict and field_types:
        # Create a dynamic TypedDict class
        # Capitalize function name and remove underscores
        class_name = f"{_snake_case_to_capital_case(func.__name__)}Return"

        # Add nested path components
        for component in nested_path:
            class_name += _snake_case_to_capital_case(_sanitize_name(component))
        return TypedDict(class_name, field_types)

    # If not a valid TypedDict, return a regular Dict with inferred types
    if dict_node.keys:
        key_types = [
            _infer_expr_type(key, symbol_table, func, nested_path + [key])
            for key in dict_node.keys
        ]
        value_types = [
            _infer_expr_type(value, symbol_table, func, nested_path)
            for value in dict_node.values
        ]

        # Determine common types
        if len(set(key_types)) == 1 and len(set(value_types)) == 1:
            return dict[key_types[0], value_types[0]]
        elif len(set(key_types)) == 1:
            return dict[key_types[0], Union[tuple(set(value_types))]]
        elif len(set(value_types)) == 1:
            return dict[Union[tuple(set(key_types))], value_types[0]]
        else:
            return dict[Union[tuple(set(key_types))], Union[tuple(set(value_types))]]

    return dict[Any, Any]


def fill_inferred_type_hints(func: Callable):
    if not getattr(func, "__annotations__", None):
        func.__annotations__ = {}

    if not "return" in func.__annotations__:
        func.__annotations__["return"] = get_return_type(func)
