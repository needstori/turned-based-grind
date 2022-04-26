from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import (NumericProperty, ObjectProperty, StringProperty)
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.popup import Popup

from functools import partial

from character import Character
from stats import Stats
from items.item import Item


class GameScreen(Screen):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game

    def update_display(self, dt):
        pass


class MainMenuScreen(GameScreen):
    farm_button = ObjectProperty(None)
    boss_button = ObjectProperty(None)
    inventory_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.farm_button.bind(on_press=self.on_farm_press)
        self.boss_button.bind(on_press=self.on_boss_press)
        self.inventory_button.bind(on_press=self.on_inventory_press)

    def on_farm_press(self, instance):
        self.game.state_transition(GameState.FARM)
        self.game.start_farming()
        self.manager.current = "farm_screen"

    def on_boss_press(self, instance):
        self.game.state_transition(GameState.BOSS)
        self.manager.current = "boss_screen"

    def on_inventory_press(self, instance):
        self.manager.current= "inventory_screen"


class FarmScreen(GameScreen):
    battle_controls = ObjectProperty(None)
    battle_display = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.current_action = None

    def on_pre_enter(self, **kwargs):
        self.battle_controls.parent_screen = self
        self.battle_controls.setup_action_buttons(self.game.player.actions)

        self.battle_display.parent_screen = self
        self.battle_display.setup_target_buttons(self.game)

    def targets_for_action(self, action):
        self.battle_display.get_targets(self.game.current_monsters)
        self.current_action = action

    def return_to_base(self, instance):
        self.game.return_to_base()
        self.manager.current = "main_menu"

    def continue_in_zone(self, instance):
        self.game.start_farming()
        self.battle_controls.setup_action_buttons(self.game.player.actions)
        self.battle_display.setup_target_buttons(self.game)

    def take_item(self, item, instance):
        if not self.game.inventory_full():
            self.game.inventory.append(item)
        else:
            # TODO: Make some good player feedback here
            print("Could not take item as inventory is full")

    # Display prompt asking if the player wants to continue in the zone or return to the main menu
    def show_zone_end_choice(self, instance):
        decision_content = GridLayout(cols=2)
        decision_continue = Button(text="Next Zone")
        decision_return = Button(text="Return to Base")
        decision_content.add_widget(decision_continue)
        decision_content.add_widget(decision_return)
        next_zone_decision = Popup(title="Zone Complete",
                                   auto_dismiss=False,
                                   content=decision_content,
                                   size_hint=(None, None),
                                   size=(400, 300))
        decision_continue.bind(on_press=next_zone_decision.dismiss)
        decision_continue.bind(on_press=self.continue_in_zone)
        decision_return.bind(on_press=next_zone_decision.dismiss)
        decision_return.bind(on_press=self.return_to_base)
        next_zone_decision.open()

    def targets_selected(self, targets):
        print(self.current_action)
        action_text = self.current_action.do_action(targets)
        self.current_action = None
        monster_action_strings = self.game.do_monster_actions()
        for action_string in monster_action_strings:
            action_text += f"\n{action_string}"
        self.battle_controls.display_action_text(action_text)
        self.battle_display.update_target_buttons(self.game)

        if self.game.zone_complete():
            # Check if item dropped and then show the item to the player
            # TODO: Make items a chance to drop
            dropped_item = Item()
            dropped_item.stats.add_stat(Stats.MAXIMUM_HEALTH, 5)
            item_drop_content = GridLayout(rows=2)
            item_display = Label(text=str(dropped_item))
            item_drop_buttons = GridLayout(cols=2)
            item_drop_content.add_widget(item_display)
            item_drop_content.add_widget(item_drop_buttons)
            item_drop_accept = Button(text="Take")
            item_drop_deny = Button(text="Discard")
            item_drop_buttons.add_widget(item_drop_accept)
            item_drop_buttons.add_widget(item_drop_deny)
            item_drop_decision = Popup(title="An Item Dropped!",
                                       auto_dismiss=False,
                                       content=item_drop_content,
                                       size_hint=(None, None),
                                       size=(400, 300))

            item_drop_accept.bind(on_press=item_drop_decision.dismiss)
            item_drop_accept.bind(on_press=partial(self.take_item, dropped_item))
            item_drop_accept.bind(on_press=self.show_zone_end_choice)
            item_drop_deny.bind(on_press=item_drop_decision.dismiss)
            item_drop_deny.bind(on_press=self.show_zone_end_choice)
            item_drop_decision.open()


class BattleDisplay(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.player_button = None
        self.monster_buttons = None
        self.parent_screen = None

    def setup_target_buttons(self, game):
        self.clear_widgets()
        self.rows = 1
        self.player_button = Button(text="Unfilled", disabled=True)
        self.add_widget(self.player_button)

        self.monster_buttons = []
        if len(game.current_monsters) > 0:
            self.cols = 2
            self.rows = len(game.current_monsters)
        for monster in game.current_monsters:
            new_monster_button = Button(text="Unfilled", disabled=True)
            new_monster_button.bind(on_press=partial(self.targets_to_parent, monster))
            self.monster_buttons.append(new_monster_button)
            self.add_widget(new_monster_button)

        self.update_target_buttons(game)

    def get_targets(self, monsters):
        for index, button in enumerate(self.monster_buttons):
            button.disabled = False

    def targets_to_parent(self, monster, instance):
        self.parent_screen.targets_selected([monster])
        for button in self.monster_buttons:
            button.disabled = True

    def update_target_buttons(self, game):
        player_button_text = f"{game.player.name}\n" \
                             f"{game.player.get_current_health()}/{game.player.get_max_health()}"
        self.player_button.text = player_button_text

        for index, monster in enumerate(game.current_monsters):
            monster_curr_health = monster.get_current_health()
            monster_max_health = monster.get_max_health()
            monster_button_text = f"{monster.name}\n{monster_curr_health}/{monster_max_health}"
            self.monster_buttons[index].text = monster_button_text


class BattleControls(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.parent_screen = None
        self.rows = 1

        self.action_grid = GridLayout(rows=2, cols=2)
        self.add_widget(self.action_grid)
        self.action_buttons = None
        self.current_actions = None
        self.big_label = Label(text="Something happened")

    def action_button_press(self, button_index, instance):
        action_to_perform = self.current_actions[button_index]
        self.parent_screen.targets_for_action(action_to_perform)
        for button in self.action_buttons:
            button.disabled = True

    def setup_action_buttons(self, actions):
        self.action_grid.clear_widgets()
        self.current_actions = actions
        self.action_buttons = []
        for i in range(4):
            new_action_button = Button(text="No Action")
            if i < len(actions):
                new_action_button.text = actions[i].name
            else:
                new_action_button.disabled = True
            new_action_button.bind(on_press=partial(self.action_button_press, i))
            self.action_grid.add_widget(new_action_button)
            self.action_buttons.append(new_action_button)

    def display_action_text(self, action_text):
        self.remove_widget(self.action_grid)
        self.add_widget(self.big_label)
        self.big_label.text = action_text
        Clock.schedule_once(self.next_action, 2)

    def next_action(self, dt):
        self.remove_widget(self.big_label)
        self.add_widget(self.action_grid)
        for i in range(len(self.current_actions)):
            self.action_buttons[i].disabled = False


class BossScreen(GameScreen):
    pass


class InventoryScreen(GameScreen):
    inventory = ObjectProperty(None)
    # TODO: Make the item slots adjust automatically to the item slots the player has
    item_weapon = ObjectProperty(None)
    item_armour = ObjectProperty(None)
    item_amulet = ObjectProperty(None)
    # TODO: Add a back button to return to the main menu from the inventory

    def on_pre_enter(self, **kwargs):
        self.inventory.setup_inventory_slots(self.game.inventory)
        self.inventory.parent_screen = self

        self.item_weapon.setup_item_slot("Weapon", self.game.player.equipped_items)
        self.item_weapon.parent_screen = self
        self.item_armour.setup_item_slot("Armour", self.game.player.equipped_items)
        self.item_armour.parent_screen = self
        self.item_amulet.setup_item_slot("Amulet", self.game.player.equipped_items)
        self.item_amulet.parent_screen = self

    def initiate_item_swap(self, item_a, button_initiated):
        self.inventory.prepare_for_item_swap()
        self.item_weapon.prepare_for_item_swap()
        self.item_armour.prepare_for_item_swap()
        self.item_amulet.prepare_for_item_swap()

        button_initiated.disabled = True


class InventoryDisplay(GridLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.parent_screen = None

        self.rows = 2
        self.cols = 2

        self.inventory_buttons = None
        self.current_inventory = None

        self.picking_mode = False

    def setup_inventory_slots(self, inventory):
        self.clear_widgets()
        self.inventory_buttons = []
        self.current_inventory = inventory
        for i in range(4):
            new_inventory_button = Button(text="Empty")
            if i < len(inventory):
                new_inventory_button.text = inventory[i].name
            else:
                new_inventory_button.disabled = True
            new_inventory_button.bind(on_press=partial(self.inventory_button_press, i))
            self.add_widget(new_inventory_button)
            self.inventory_buttons.append(new_inventory_button)

    def inventory_button_press(self, item_index, instance):
        # TODO: Make these buttons state based so they will react differently in different states of the
        #   overall display, less confusing binding and unbinding that way.
        self.parent_screen.initiate_item_swap(self.current_inventory[item_index], instance)
        pass

    def prepare_for_item_swap(self):
        for i in range(4):
            button = self.inventory_buttons[i]
            button.disabled = False
            # TODO: unbind stuff :S


class ItemSlot(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.parent_screen = None

        self.rows = 2

        self.slot_id = None
        self.slot_label = None
        self.slot_button = None

    def setup_item_slot(self, slot_id, item_slots):
        self.clear_widgets()
        self.slot_id = slot_id
        self.slot_label = Label(text=slot_id,
                                size_hint_y=1)
        self.slot_button = Button(text="Empty",
                                  size_hint_y=4)
        slot_item = item_slots.get_item(slot_id)
        if slot_item is not None:
            self.slot_button.text = str(slot_item)
        else:
            self.slot_button.text = "Empty"
            self.slot_button.disabled = True
        self.add_widget(self.slot_label)
        self.add_widget(self.slot_button)

    def prepare_for_item_swap(self):
        self.slot_button.disabled = False


class GameState:
    IDLE = 'idle'
    FARM = 'farm'
    BOSS = 'boss'


# Holds all of the game state so it can be more easily shared between all of the game screens.
class CramGame:
    def __init__(self):
        self.player = None
        self.inventory = None
        self.inventory_size = 4
        self.current_state = GameState.IDLE
        self.current_monsters = None
        self.zone = None

        self.create_player()
        self.load_inventory()

    def create_player(self):
        self.player = Character()
        self.player.stats.add_stat(Stats.MIN_DAMAGE, 3)
        self.player.stats.add_stat(Stats.MAX_DAMAGE, 5)
        self.player.name = "Player"

    def load_inventory(self):
        self.inventory = []
        # TODO: Remove this code that adds and item for testing
        dropped_item = Item()
        dropped_item.stats.add_stat(Stats.MAXIMUM_HEALTH, 5)
        self.inventory.append(dropped_item)

    def start_farming(self):
        self.current_monsters = []
        new_monster = Character()
        new_monster.name = "Monster"
        self.current_monsters.append(new_monster)

    def return_to_base(self):
        self.player.full_restore()
        self.state_transition(GameState.IDLE)

    def do_monster_actions(self):
        monster_action_strings = []
        for monster in self.current_monsters:
            if monster.alive():
                monster_action_strings.append(monster.actions[0].do_action([self.player]))
        return monster_action_strings

    def zone_complete(self):
        for monster in self.current_monsters:
            if monster.alive():
                return False
        return True

    def inventory_full(self):
        return len(self.inventory) == self.inventory_size

    def state_transition(self, new_state):
        old_state = self.current_state

        self.current_state = new_state


class CramGameApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.screen_manager = None
        self.game = None

    def build(self):
        self.game = CramGame()

        self.screen_manager = ScreenManager()
        main_menu_screen = MainMenuScreen(game=self.game, name="main_menu")
        self.screen_manager.add_widget(main_menu_screen)

        farm_screen = FarmScreen(game=self.game, name="farm_screen")
        self.screen_manager.add_widget(farm_screen)

        boss_screen = BossScreen(game=self.game, name="boss_screen")
        self.screen_manager.add_widget(boss_screen)

        inventory_screen = InventoryScreen(game=self.game, name="inventory_screen")
        self.screen_manager.add_widget(inventory_screen)

        return self.screen_manager




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    CramGameApp().run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
