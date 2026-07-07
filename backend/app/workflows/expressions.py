import ast
import operator
from typing import Dict, Any


class ExpressionEngine:
    """Secure expression evaluator based on python AST."""
    
    # Supported operators
    _ops = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
    }

    @classmethod
    def evaluate(cls, expression: str, context: Dict[str, Any]) -> bool:
        if not expression:
            return True
            
        try:
            tree = ast.parse(expression, mode='eval')
            return cls._eval_node(tree.body, context)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression '{expression}': {e}")

    @classmethod
    def _eval_node(cls, node, context: Dict[str, Any]):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            raise ValueError(f"Variable '{node.id}' not found in context")
        elif isinstance(node, ast.Attribute):
            obj = cls._eval_node(node.value, context)
            if isinstance(obj, dict):
                return obj.get(node.attr)
            return getattr(obj, node.attr)
        elif isinstance(node, ast.Compare):
            left = cls._eval_node(node.left, context)
            for op, right in zip(node.ops, node.comparators):
                right_val = cls._eval_node(right, context)
                op_func = cls._ops.get(type(op))
                if not op_func:
                    raise ValueError(f"Unsupported operator: {type(op)}")
                left = op_func(left, right_val)
                if not left:
                    return False
            return True
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(cls._eval_node(val, context) for val in node.values)
            elif isinstance(node.op, ast.Or):
                return any(cls._eval_node(val, context) for val in node.values)
                
        raise ValueError(f"Unsupported AST node: {type(node)}")
