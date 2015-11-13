# -*- coding: utf-8 -*-


class XNTechTreeItem:
    def __init__(self, gid=None, name=None, category=None):
        self.gid = 0
        self.name = ''
        self.category = ''
        if gid is not None:
            self.gid = gid
        if name is not None:
            self.name = name
        if category is not None:
            self.category = category

    def __str__(self):
        return self.name

    def __repr__(self):
        return "XNTechTreeItem({0}, '{1}', '{2}'".format(
            self.gid, self.name, self.category)


class XNTechTree:
    def __init__(self):
        self._is_initialized = False
        self._tt_gid_map = dict()
        self._tt_name_map = dict()

    def is_initialized(self) -> bool:
        return self._is_initialized

    def init_techtree(self, tt_list: list):
        # tt - list of tuples (gid, name, category)
        if len(tt_list) < 1:
            return
        self._is_initialized = True
        for tt_tuple in tt_list:
            item = XNTechTreeItem(tt_tuple[0], tt_tuple[1], tt_tuple[2])
            self._tt_gid_map[tt_tuple[0]] = item
            self._tt_name_map[tt_tuple[1]] = item

    def find_item_by_name(self, name: str) -> XNTechTreeItem:
        if not self._is_initialized:
            return None
        if name in self._tt_name_map:
            return self._tt_name_map[name]
        return None

    def find_item_by_gid(self, gid: int) -> XNTechTreeItem:
        if not self._is_initialized:
            return None
        if gid in self._tt_gid_map:
            return self._tt_gid_map[gid]
        return None

    def find_gid_by_name(self, name: str) -> int:
        tt_item = self.find_item_by_name(name)
        if tt_item is None:
            return 0  # not found
        return tt_item.gid


_singleton_techtree_instance = None


def XNTechTree_instance() -> XNTechTree:
    global _singleton_techtree_instance
    if _singleton_techtree_instance is None:
        _singleton_techtree_instance = XNTechTree()
    return _singleton_techtree_instance
