from stat_holder import StatHolder


class Item:
    def __init__(self):
        self.stats = StatHolder()

        self.name = "Item Name"

    def __str__(self):
        item_string = self.name
        for stat_name, stat_value in self.stats.get_existing_stats():
            item_string += "\n"
            item_string += f"{stat_name}: {stat_value}"
        return item_string
