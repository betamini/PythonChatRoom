from callback_handler import BasicCallCodes
import random

class RoomManager():
    def __init__(self, item_manager):#, callback_handler):
        self._item_map = dict()
        self.item_manager = item_manager
        self.rootroom = Room(None)
        #self.callback_handler = callback_handler

    def get_all_items(self):
        return self._item_map.keys()

    def move_to(self, source_item, destination_item, place_in_new_room_if_already_in_same=True):
        if source_item in self._item_map:
            source_room = self._item_map[source_item]
            if destination_item in self._item_map:
                destination_room = self._item_map[destination_item]

                if destination_room == source_room and place_in_new_room_if_already_in_same:
                    sub_room = Room(destination_room)
                    self._move_element_to_room(source_item, sub_room)
                    self._move_element_to_room(destination_item, sub_room)
                else:
                    self._move_element_to_room(source_item, destination_room)
            else:
                print("Destination is not in _item_map")
        else:
            print("Source is not in _item_map")
        
    def exit_room(self, item):
        if item in self._item_map:
            curr_room = self._item_map[item]

            if curr_room != self.rootroom:
                self._move_element_to_room(item, curr_room.parent)

    def add_item(self):
        item = Item(self.item_manager)

        self._item_map[item] = self.rootroom

        self.rootroom.add_item(item)
        return item

    def remove_item(self, item):
        if item in self._item_map:
            room = self._item_map[item]
            del self._item_map[item]
            self.item_manager.delete_item(item)

            room.remove_item(item)
    
    def _move_element_to_room(self, item, room):
        # if room specified is not a Room class exit
        if not isinstance(room, Room):
            print(f"Can't move element to an object not of type Room  Given Type:{type(room)}  Value:{room}")
            #self.callback_handler.run(BasicCallCodes.LOG_WARNING, f"Can't move element to an object not of type Room  Given Type:{type(room)}")
        # if id specified translates to an element in _item_map move element
        elif item in self._item_map:
            prev_room = self._item_map[item]
            # only move if not already in specified room
            if prev_room != room:
                room.add_item(item)
                prev_room.remove_item(item)
                self._item_map[item] = room
        else:
            print(f"Can't move element {item}, element is not in _item_map")
            #self.callback_handler.run(BasicCallCodes.LOG_WARNING, f"Can't move element with id {unique_id}, element is not in _item_map")

    #def get_unique_id(self):
    #    uid = random.randint(100,999)
    #    if uid in self._item_map:
    #        return self.get_unique_id()
    #    else:
    #        return uid
    def get_structure(self):
        return self.rootroom.get_structure()

    def get_items_near(self, item, allow_recursive_down_search):
        if item in self._item_map:
            element_room = self._item_map[item]
            elements, rooms = element_room.get_all_contents(allow_recursive_down_search)
            elements.remove(item)
            return elements
            
    def remove_room(self, room):
        if room != self.rootroom:
            items, realoc_room = room.terminate()

            for item in items:
                self._item_map[item] = realoc_room
    
    def print_formated(self):
        print("\nRoom Manager Structure")
        self.rootroom.print_formated(1)
    
    # def move_to_new_room(self, iterable):
    #     curr_room = None
    #     valid_elements = list()
    #     is_in_same_room = True

    #     for elem in iterable:
    #         if elem in self._item_map:
    #             if curr_room != self._item_map[elem] and curr_room != None:
    #                 is_in_same_room = False
    #             else:
    #                 curr_room = self._item_map[elem]
    #             valid_elements.append(elem)
        
    #     new_room = None
        
    #     if is_in_same_room:
    #         new_room = Room(curr_room)
    #     else:
    #         new_room = Room(self.rootroom)
        
    #     for elem in valid_elements:
    #         self._move_element_to_room(elem, new_room)

class Room():
    def __init__(self, parent):
        #super().__init__()
        self.items = dict()
        self.sub_rooms = dict()

        self.parent = parent
        if self.parent != None:
            self.parent.add_room(self)
    
    def is_empty(self):
        if len(self.items) == 0 and len(self.sub_rooms) == 0:
            return True
        else:
            return False

    def add_item(self, hashable_item):
        self.items[hashable_item] = hashable_item
    
    def add_items(self, *args):
        self.items.update(*args)

    def remove_item(self, hashable_item):
        try:
            del self.items[hashable_item]
            if self.is_empty():
                self.terminate()
            return True
        except KeyError as e:
            return False

    def add_room(self, hashable_room):
        self.sub_rooms[hashable_room] = hashable_room

    def remove_room(self, hashable_room):
        try:
            del self.sub_rooms[hashable_room]
            if self.is_empty():
                self.terminate()
            return True
        except KeyError as e:
            return False

    def get_all_contents(self, allow_recursive_down_search):
        items = set(self.items)
        rooms = set(self.sub_rooms)
        if allow_recursive_down_search:
            for room in self.sub_rooms:
                _items, _rooms = room.get_all_contents(True)
                rooms.update(_rooms)
                items.update(_items)
        return (items, rooms)

    def get_structure(self):
        structure = list(self.items)
        for room in self.sub_rooms:
            structure.append(room.get_structure())
        return structure

    def print_formated(self, level):
        line = "|"
        room_symbol = "v"
        indent = ""
        if level > 1:
            indent += (line + " ") * (level - 1)
        for item in self.items:
            print(indent + str(item.data))
        for room in self.sub_rooms:
            print(indent + room_symbol)
            room.print_formated(level + 1)

    def terminate(self):
        if self.parent != None:
            items, rooms = self.get_all_contents(True)
            for room in rooms:
                del room.sub_room
                del room.items
                del room
            self.parent.add_items((items))
            self.parent.remove_room(self)

            del self.items
            del self.sub_rooms

            # Return the elements that have been relocated and location they relocated to
            return (items, self.parent)


class ItemManager():
    def __init__(self):
        self._datakey_to_item = dict()

    def link_datakey_to_item(self, datakey, item):
        if datakey not in self._datakey_to_item:
            self._datakey_to_item[datakey] = item
        else:
            if self._datakey_to_item[datakey] != item:
                raise Exception(f"datakey ({datakey}) is already linked to {self._datakey_to_item[datakey]}, cant link to {item}")

    def delink_datakey_to_item(self, datakey):
        del self._datakey_to_item[datakey]

    def get_item(self, datakey_or_item):
        if isinstance(datakey_or_item, Item):
            return datakey_or_item
        else:
            return self._datakey_to_item.get(datakey_or_item, None)
    
    def delete_item(self, item):
        item.datakey = set()
        del item


class Item():
    def __init__(self, item_manager):
        self.item_manager = item_manager
        self._datakey = set()

    @property
    def datakey(self): return self._datakey
    
    @datakey.setter
    def datakey(self, value):
        prev_keys = self._datakey

        self._datakey = set(value)
        new_keys = self._datakey


        removed_keys = prev_keys - new_keys
        for key in removed_keys:
            self.item_manager.delink_datakey_to_item(key)

        added_keys = new_keys - prev_keys
        for key in added_keys:
            self.item_manager.link_datakey_to_item(key, self)
    
    @datakey.deleter
    def datakey(self): del self._datakey


    @property
    def data(self): return self._data
    
    @data.setter
    def data(self, value):
        self._data = value
    
    @data.deleter
    def data(self): del self._data


#room_manager = RoomManager()

#print(room_manager.add_elements([1, 2, 3, 4, 5, 6, 7]))

#room_manager.move_to_new_room([3,5])

#room_manager.move_to(1, 4)
#room_manager.move_to(5, 4)
#room_manager.move_to(5, 4)
#oom_manager.move_to(2, 3)

#prev_room = Room(None)
#rooms = set([prev_room])
#for x in range(0, 10):
#   prev_room = Room(prev_room)
#   rooms.add(prev_room)

#a = list([2, 4])
#print(type(a.__hash__))
#print(a.__hash__())

#prev_room.parent.parent.terminate()


#print(Room(20, None).__hash__())

#room_manager.print_formated()