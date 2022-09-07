import enum
import os
import re
from typing import Dict, List, Union

from utils import argmax_all, quote, unquote


class AssetType(enum.Enum):
    Directory = enum.auto()
    Image = enum.auto()
    Document = enum.auto()
    Unknown = enum.auto()

    @staticmethod
    def from_asset_path(abspath: str) -> 'AssetType':
        if os.path.isdir(abspath):
            return AssetType.Directory
        else:
            return AssetType.from_ext(os.path.splitext(abspath)[-1])

    @staticmethod
    def from_ext(ext: str) -> 'AssetType':
        if ext in ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG', '.bmp', '.BMP']:
            return AssetType.Image
        elif ext in ['.md', '.MD']:
            return AssetType.Document
        else:
            return AssetType.Unknown


class AssetNode(object):
    def __init__(self, name: str, abspath: str, depth: int, type: AssetType = None):
        self.name: str = name
        self.abspath:str = abspath
        self.depth: int = depth
        self.type: AssetType = type if type is not None else AssetType.from_asset_path(abspath)
        self.children: List[AssetNode] = []
        self.parent: AssetNode = None

    def add_child(self, child: 'AssetNode') -> None:
        self.children.append(child)
        child.parent = self

    def find_child(self, name: str) -> 'AssetNode':
        for child in self.children:
            if child.name == name:
                return child

    def find_ref_node(self, path: str) -> 'AssetNode':
        path = path.split('/')
        node: AssetNode = self
        for name in path:
            if name == '..':
                node = node.parent
                if node is None:
                    break
            elif name == '.' or name == '':
                pass
            else:
                node = node.find_child(name)
                if node is None:
                    break

        return node

    def find_nearest(self, name: str, tree: 'AssetTree') -> List['AssetNode']:
        lca_depths = [self._lca(node).depth for node in tree.node_index[name]]
        return [tree.node_index[name][i] for i in argmax_all(lca_depths)]

    def get_ref_path(self, ref_node: 'AssetNode') -> str:
        lca = self._lca(ref_node)
        path = ['..'] * (self.depth - lca.depth - 1)
        node_path = [ref_node]
        while node_path[0].parent != lca:
            node_path.insert(0, node_path[0].parent)
        path += [node.name for node in node_path]
        return '/'.join(path)

    def _lca(self, other: 'AssetNode') -> 'AssetNode':
        node = self
        while node != other and node.depth > 0:
            if other.depth > node.depth:
                other = other.parent
            elif node.depth > other.depth:
                node = node.parent
            else:
                node = node.parent
                other = other.parent

        return node


class AssetTree(object):
    def __init__(self, root_path: str):
        self.root_path: str = root_path
        self.node_index: Dict[str, List[AssetNode]] = {}
        self.root_node: AssetNode = self._build(root_path, 0)

    def _build(self, abspath: str, depth: int) -> AssetNode:
        name = os.path.basename(abspath)
        node = AssetNode(name, abspath, depth)

        if node.type == AssetType.Directory:
            filelist = os.listdir(abspath)
            for filename in filelist:
                filepath = os.path.join(abspath, filename)
                node.add_child(self._build(filepath, depth + 1))

        if name in self.node_index:
            self.node_index[name].append(node)
        else:
            self.node_index[name] = [node]

        return node

    def tree_string(self) -> str:
        return self._tree_string_helper(self.root_node)

    def _tree_string_helper(self, node: AssetNode) -> str:
        tree_string = '  ' * node.depth + node.name + ' - ' + str(node.type) + '\n'
        for child in node.children:
            tree_string += self._tree_string_helper(child)
        return tree_string


class AssetExplorer(object):
    def __init__(self, tree: AssetTree):
        self.tree: AssetTree = tree
        self.current: AssetNode = tree.root_node
        self.path = [tree.root_node.name]

    def goto_root(self) -> None:
        self.current = tree.root_node
        self.path = [tree.root_node.name]

    def goto_parent(self) -> bool:
        if self.current == self.tree.root_node:
            return False
        self.current = self.current.parent
        self.path.pop()
        return True

    def goto_child_index(self, idx: Union[int, str]) -> bool:
        if isinstance(idx, str) and not idx.isalnum():
            return False

        idx = int(idx)

        if idx < 0 or idx >= len(self.current.children):
            return False

        self.current = self.current.children[idx]
        self.path.append(self.current.name)
        return True

    def goto_child(self, name: str) -> bool:
        child = self.current.find_child(name)
        if child == None:
            return False

        self.current = child
        self.path.append(name)
        return True

    def goto_ref_node(self, path: str) -> bool:
        ref_node = self.current.find_ref_node(path)
        if ref_node is None:
            return False

        self.current = ref_node

        node_path = [self.current]
        while node_path[0].parent is not None:
            node_path.insert(0, node_path[0].parent)
        self.path = [node.name for node in node_path]

        return True

    def cmd_list(self):
        print('Current node:', '/'.join(self.path))
        for i, child in enumerate(self.current.children):
            print(str(i).rjust(3), '|', child.name)

    def cmd_change_node(self, arg: str):
        if arg == '..':
            if not self.goto_parent():
                print('Root node has no parent.')
        elif arg == '.':
            pass
        elif arg == '/' or arg == '~':
            self.goto_root()
        elif self.goto_child_index(arg):
            pass
        elif self.goto_child(arg):
            pass
        elif self.goto_ref_node(arg):
            pass
        else:
            print('Error')


def repair_ref_images(tree: AssetTree, doc_node: AssetNode):
    print('repairing', doc_node.abspath)
    swap_filepath = doc_node.abspath + '.swap'
    backup_file_path = doc_node.abspath + '.bak'
    matcher = re.compile(r'!\[.*\]\((.*)\)')

    def repair_ref(matched: re.Match):
        path = matched[1]

        ref_node = doc_node.find_ref_node(unquote(path).replace('\\', '/'))
        if ref_node is not None:
            return matched[0]

        nearest_nodes = doc_node.find_nearest(unquote(os.path.basename(path)), tree)
        if len(nearest_nodes) == 0:
            return matched[0]
        elif len(nearest_nodes) == 1:
            return matched[0].replace(path, quote(doc_node.get_ref_path(nearest_nodes[0])))

        for node in nearest_nodes:
            if doc_node.name.split('.')[0] in node.abspath:
                return matched[0].replace(path, quote(doc_node.get_ref_path(node)))

        return matched[0]

    with open(doc_node.abspath, encoding='utf-8') as read_f, open(swap_filepath, 'w', encoding='utf-8') as write_f:
        for i, line in enumerate(read_f):
            matched = matcher.match(line)
            if matched is not None:
                repaired = repair_ref(matched)
                if matched[0] != repaired:
                    print(str(i).rjust(3), '|', matched[0], '->', repaired)
                    line = line.replace(matched[0], repaired)
            write_f.write(line)

    if os.path.exists(backup_file_path):
        os.remove(backup_file_path)
    os.rename(doc_node.abspath, backup_file_path)
    os.rename(swap_filepath, doc_node.abspath)


if __name__ == '__main__':
    workspace_dir = input('Workspace dir: ')
    tree = AssetTree(workspace_dir)
    explorer = AssetExplorer(tree)
    while True:
        cmd = input('>> ')
        cmd = cmd.split(maxsplit=1)
        if len(cmd) == 0:
            pass
        elif cmd[0] in ['list', 'ls', 'cn'] and len(cmd) == 1:
            explorer.cmd_list()
        elif cmd[0] == 'exit' and len(cmd) == 1:
            break
        elif cmd[0] in ['change-node', 'cn'] and len(cmd) == 2:
            explorer.cmd_change_node(cmd[1])
        elif cmd[0] in ['repair-ref-images', 'rri'] and len(cmd) == 1:
            repair_ref_images(tree, explorer.current)
        else:
            print('Error')
