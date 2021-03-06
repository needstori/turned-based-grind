class ItemSlotSet:
    def __init__(self, set_type):
        self.item_slots = {}
        if set_type == ItemSlotSetTypes.HUMAN:
            self.item_slots["Weapon"] = None
            self.item_slots["Armour"] = None
            self.item_slots["Amulet"] = None

    def get_item(self, item_slot_id):
        # TODO: Add error handling
        if item_slot_id in self.item_slots.keys():
            return self.item_slots[item_slot_id]
        else:
            return None


class ItemSlotSetTypes:
    HUMAN = "Human"
