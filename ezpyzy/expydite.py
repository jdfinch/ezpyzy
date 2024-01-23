"""
Problem: Debugging environment doesn't work due to IDE bugs, remote development, terminal-based development, etc.

Solution: Run the code once, re-compiling and re-running only lines after the first change (changes tracked on the top module level only). Allows for some limited interactive debugging and variable inspection, without a debugger. Particularly useful when some resource, like a deep learning model, must be loaded first in order to debug. The model now only needs to be loaded once at the top of the module; then re-running code after changes is fast and easy.
"""

import ast
import difflib as dl
import inspect as ins
import textwrap as tw
import pathlib as pl
import types as ty
import traceback as tb
import sys

empty = ty.ModuleType('empty_module')
empty.__annotations__ = {}
empty.__file__ = None
empty.__cached__ = None

no_expression = object()

already_executing = False

to_end = object()
everything = lambda name, value, node: True
def values_only(name, value, node):
    return not (ins.ismodule(value) or ins.isfunction(value) or ins.isclass(value))


def explore(
    expression=no_expression,
    max_rows=None,
    max_value_length=to_end,
    max_col=80,
    including=values_only,
    show_entire_last_variable=None,
    show_members_of_self=True,
    exit=True
):
    frame = ins.currentframe()
    caller_frame = frame.f_back
    frame_name = caller_frame.f_code.co_name
    if  frame_name == '<module>':
        frame_name = 'main'
    line_no = caller_frame.f_lineno
    module = ins.getmodule(caller_frame)
    file = pl.Path(ins.getsourcefile(module))
    code = file.read_text()
    caller_globals = caller_frame.f_globals
    caller_locals = caller_frame.f_locals
    variables = get_ranked_variables(
        caller_globals, caller_locals, expression,
        module_code=code,
        before_index=line_no,
        including=including,
        show_members_of_self=show_members_of_self,
    )
    if show_entire_last_variable is None:
        show_entire_last_variable = expression is not no_expression
    display_variables(variables,
        max_rows=max_rows,
        max_value_length=max_value_length,
        max_col=max_col,
        show_entire_last_variable=show_entire_last_variable,
    )
    print(f'{frame_name} in File "{file}", line {line_no} Explored')
    if exit and already_executing:
        raise ExitingExploration()
    elif exit:
        execute(module, max_col=max_col)
        quit()


def execute(module=None, max_col=80):
    global already_executing
    if already_executing:
        return
    already_executing = True
    if module is None:
        frame = ins.currentframe()
        caller = frame.f_back
        module = ins.getmodule(caller)
    caller_file = pl.Path(ins.getsourcefile(module))
    old_code = caller_file.read_text()
    while True:
        command = input('|> ')
        print('=' * max_col)
        new_code = caller_file.read_text()
        execute_affected_code(old_code, new_code, module)
        old_code = new_code


def execute_affected_code(old_code, new_code, module=None):
    differences = line_differences(old_code, new_code)
    affected_line = None
    new_ast = ast.parse(new_code)
    for old_start, old_end, new_start, new_end in differences:
        affected_line = get_first_affected_line(new_ast, new_start)
        break
    if affected_line is not None:
        affected_code_lines = new_code.splitlines()[affected_line:]
        affected_code = '\n'.join(affected_code_lines)
        affected_code = '\n' * affected_line + affected_code
        namespace = execute_python_code(affected_code, module)
        return namespace
    return {}


def line_differences(string1, string2):
    blocks = {}
    lines1 = string1.splitlines(True)
    lines2 = string2.splitlines(True)
    matcher = dl.SequenceMatcher(None, lines1, lines2)
    for op, i1, j1, i2, j2 in matcher.get_opcodes():
        if op != 'equal':
            diff1 = lines1[i1:j1]
            diff2 = lines2[j1:j2]
            blocks[(i1, j1, i2, j2)] = (diff1, diff2)
    return blocks


def get_first_affected_line(code_ast, changed_line_index):
    global_elements = {}
    def process_node(node):
        if isinstance(node, (ast.stmt, ast.FunctionDef, ast.ClassDef)):
            if hasattr(node, 'lineno'):
                start_and_end =  (node.lineno - 1, node.end_lineno)
                global_elements[start_and_end] = node
        else:
            for child_node in ast.iter_child_nodes(node):
                process_node(child_node)
    process_node(code_ast)
    affected_line = None
    for (start, end), element in sorted(global_elements.items()):
        if changed_line_index < end:
            affected_line = start
            break
    return affected_line


def execute_python_code(code, module=None):
    module_namespace = {} if module is None else module.__dict__
    program = compile(code, module.__file__, 'exec', dont_inherit=True)
    try:
        exec(program, module_namespace)
    except ExitingExploration:
        pass
    except Exception:
        tb.print_exc(file=sys.stderr)
    updated_namespace = {
        variable: value for variable, value in module_namespace.items()
        if variable not in empty.__dict__
    }
    return updated_namespace


def get_ranked_variables(
    globals_dict,
    locals_dict,
    expression=no_expression,
    module_code=None,
    before_index=None,
    including=values_only,
    show_members_of_self=True,
    max_expression_items=3,
):
    excluded_globals = dir(empty)
    variables = {}  # name -> value
    for name, value in globals_dict.items():
        if name not in excluded_globals:
            variables[name] = value
    for name, value in locals_dict.items():
        if name not in excluded_globals:
            if show_members_of_self and name == 'self':
                variables.update({
                    f'self.{mem_name}': mem_value
                    for mem_name, mem_value in value.__dict__.items()
                })
            variables[name] = value
    assigned_vars, nodes = get_vars_in_order_of_last_assignment(
        module_code, before_index
    )
    if 'self' in variables:
        for name in variables:
            if name.startswith('self.'):
                assigned_vars[name] = assigned_vars.get('self', float('-inf')) - 0.75
            elif name == 'self':
                assigned_vars[name] = assigned_vars.get('self', float('-inf')) - 0.5
    var_ranking = sorted(
        [
            (assigned_vars.get(name, float('-inf')), name)
            for name in variables
        ]
    )
    filtered_var_ranking = [
        (line_no, name)
        for line_no, name in var_ranking
        if name in variables and including(name, variables[name], nodes.get(name))
    ]
    ranked_vars_values = {
        name: variables[name] for _, name in filtered_var_ranking
    }
    if expression is not no_expression:
        items = None
        if not ins.isgenerator(expression):
            try:
                items = list(enumerate(expression)) # noqa
                items = [(item, expression[item]) for _, item in items] # noqa
            except Exception:
                pass
        members = {}
        if items is not None:
            displayed_items = [(f'ex[{i}]', item) for i, item in items]
            if len(displayed_items) > max_expression_items:
                displayed_items = displayed_items[:max_expression_items]
            members.update(displayed_items)
            members['len(ex)'] = len(items)
        try:
            members.update(reversed([
                (f'ex.{n}', v) for n, v in expression.__dict__.items() if not n.startswith('_')]
            ))
        except Exception:
            pass
        members['ex'] = expression
        ranked_vars_values.update({
            name: value for name, value in members.items()
            if including(name, value, None)
        })
    return ranked_vars_values


def get_vars_in_order_of_last_assignment(module_code: str, before_index=None):
    if not module_code:
        return {}, {}
    tree = ast.parse(module_code)
    assigned_vars = {}  # var_name -> line_no
    assigned_nodes = {}  # var_name -> node
    def visit_assign(node):
        if isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            line_no = node.lineno
            if before_index is None or line_no < before_index:
                if line_no > assigned_vars.get(name, float('-inf')):
                    assigned_vars[name] = line_no
                    assigned_nodes[name] = node
    def visit_for(node):
        if hasattr(node, 'response') and isinstance(node.response, ast.Name):
            name = node.response.id
            line_no = node.lineno
            if before_index is None or line_no < before_index:
                if line_no > assigned_vars.get(name, float('-inf')):
                    assigned_vars[name] = line_no
                    assigned_nodes[name] = node
        elif hasattr(node, 'iter') and isinstance(node.iter, ast.Name):
            name = node.iter.id
            line_no = node.lineno
            if before_index is None or line_no < before_index:
                if line_no > assigned_vars.get(name, float('-inf')):
                    assigned_vars[name] = line_no
                    assigned_nodes[name] = node
    def visit_function(node):
        for arg in node.args.args:
            if isinstance(arg, ast.arg):
                name = arg.arg
                line_no = arg.lineno
                if before_index is None or line_no < before_index:
                    if line_no > assigned_vars.get(name, float('-inf')):
                        assigned_vars[name] = line_no
                        assigned_nodes[name] = node
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            visit_assign(node)
        elif isinstance(node, ast.For):
            visit_for(node)
        elif isinstance(node, ast.FunctionDef):
            visit_function(node)
    return assigned_vars, assigned_nodes


def display_variables(
    variables,
    max_rows=None,
    max_col=80,
    max_value_length=to_end,
    show_entire_last_variable=False,
):
    if not variables:
        return
    displayed_vars_vals = list(variables.items())
    max_name_length = max(len(name) for name in list(zip(*displayed_vars_vals))[0])
    max_val_col_length = max_col - max_name_length - 3
    if max_value_length is to_end:
        max_value_length = max_val_col_length
    print('-' * max_col)  # Line boundary
    if max_rows and len(displayed_vars_vals) > max_rows:
        displayed_vars_vals = displayed_vars_vals[-max_rows:]
    for i, (name, value) in enumerate(displayed_vars_vals):
        name_str = f"{name}:"
        value_str = str(value)
        if ((
                show_entire_last_variable and i < len(displayed_vars_vals)-1
                or not show_entire_last_variable
            ) and max_value_length and len(value_str) > max_value_length
        ):
            value_str = value_str[:max_value_length - 3] + '...'
        value_lines = tw.wrap(value_str, width=max_val_col_length)
        print(f"{name_str.ljust(max_name_length + 2)} {value_lines[0] if value_lines else ''}")
        for line in value_lines[1:]:
            print(f"{''.ljust(max_name_length + 2)} {line}")
        print('-' * max_col)  # Line boundary


class ExitingExploration(BaseException):
    pass
