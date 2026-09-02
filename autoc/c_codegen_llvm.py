from pycparser import c_ast

from .ast import Assignment, BinaryOp, Call, ExprStmt, FunctionDef, IfStmt, Name, Number, Param, Program, ReturnStmt, UnaryOp, VarDecl, WhileLoop
from .llvm_codegen import LLVMCodeGenerator


class CLLVMError(ValueError):
    pass


class CToAutoCAST:
    def type_name(self, node):
        if isinstance(node, c_ast.TypeDecl):
            return node.type.names[-1]
        if isinstance(node, c_ast.PtrDecl):
            return "str"
        return "int"

    def expression(self, node):
        if node is None:
            return Number(0)
        if isinstance(node, c_ast.Constant):
            if node.type in {"int", "char"}:
                return Number(int(node.value.strip("'")))
            if node.type in {"float", "double"}:
                return Number(float(node.value))
            return Name(node.value)
        if isinstance(node, c_ast.ID):
            return Name(node.name)
        if isinstance(node, c_ast.BinaryOp):
            return BinaryOp(node.op, self.expression(node.left), self.expression(node.right))
        if isinstance(node, c_ast.UnaryOp):
            return UnaryOp({"p++": "+", "p--": "-"}.get(node.op, node.op), self.expression(node.expr))
        if isinstance(node, c_ast.FuncCall):
            args = [] if node.args is None else [self.expression(arg) for arg in node.args.exprs]
            return Call(self.expression(node.name).id, args)
        raise CLLVMError("Unsupported C expression: %s" % type(node).__name__)

    def statements(self, node):
        if isinstance(node, c_ast.Compound):
            result = []
            for item in node.block_items or []:
                result.extend(self.statements(item))
            return result
        if isinstance(node, c_ast.Decl):
            return [VarDecl(node.name, self.expression(node.init) if node.init else None, self.type_name(node.type))]
        if isinstance(node, c_ast.Return):
            return [ReturnStmt(self.expression(node.expr) if node.expr else None)]
        if isinstance(node, c_ast.Assignment):
            if not isinstance(node.lvalue, c_ast.ID):
                raise CLLVMError("Only named assignment targets are supported")
            value = self.expression(node.rvalue)
            if node.op != "=":
                value = BinaryOp(node.op[:-1], Name(node.lvalue.name), value)
            return [Assignment(node.lvalue.name, value)]
        if isinstance(node, c_ast.FuncCall):
            return [ExprStmt(self.expression(node))]
        if isinstance(node, c_ast.If):
            else_block = self.statements(node.iffalse) if node.iffalse else None
            return [IfStmt(self.expression(node.cond), self.statements(node.iftrue), else_block)]
        if isinstance(node, c_ast.While):
            return [WhileLoop(self.expression(node.cond), self.statements(node.stmt))]
        raise CLLVMError("Unsupported C statement: %s" % type(node).__name__)

    def convert(self, tree):
        functions = []
        for node in tree.ext:
            if not isinstance(node, c_ast.FuncDef):
                continue
            params = []
            if node.decl.type.args:
                params = [Param(param.name, self.type_name(param.type)) for param in node.decl.type.args.params if getattr(param, "name", None)]
            return_type = self.type_name(node.decl.type.type)
            functions.append(FunctionDef(node.decl.name, params, return_type, self.statements(node.body)))
        return Program(functions)


def compile_c_to_llvm(tree):
    return LLVMCodeGenerator().emit_program(CToAutoCAST().convert(tree))
