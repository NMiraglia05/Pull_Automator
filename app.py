from flask import Flask, render_template, request, jsonify, url_for
from collections import Counter
import copy
import re
import math

app=Flask(__name__)

pivoted_items = {
    'mining': {
        'coal': {'points': 1},
        'salt': {'points': 1},
        'stone': {'points': 1},
        'iron': {'points': 2},
        'quartz': {'points': 2},
        'copper': {'points': 2},
        'marble': {'points': 2},
        'mercury': {'points': 3},
        'sulfur': {'points': 3},
        'silver': {'points': 3},
        'manganese': {'points': 3},
        'obsidian': {'points': 4},
        'gold': {'points': 4},
        'soul gem': {'points': 4},
        'spell crystal': {'points': 4}
    },
    'hunting': {
        'bone': {'points': 1},
        'feathers': {'points': 1},
        'honey': {'points': 1, 'expiration': '1 month'},
        'food': {'points': 1, 'expiration': '1 month'},
        'soft pelt': {'points': 2},
        'demon blood': {'points': 2},
        'large hide': {'points': 3},
        'celestial blood': {'points': 3},
        'fae blood': {'points': 4}
    },
    'mercantile': {
        'cloth': {'points': 1},
        '5 postage (domestic)': {'points': 1},
        'paper': {'points': 1},
        'glass': {'points': 2},
        'blood ink': {'points': 2},
        '5 postage (overseas)': {'points': 2},
        'sanctified water': {'points': 3},
        'ritual component': {'points': 4}
    },
    'black_market': {
        'zye scarab': {'points': 3},
        'zye blood parasites': {'points': 4}
    }
}

alternates={
    'blood ink':'black_market',
    'bone':'black_market'
}

crafted_item_lookup={'Animal Traps': {'iron': 3},
                'Cooking Pot': {'copper': 3, 'wood(strong+durable)': 1},
                "Gardener's Tools": {'iron': 2, 'wood(strong+durable)': 1},
                "Mason's Chisel": {'iron': 3, 'wood(strong+durable)': 1},
                "Surgeon's Razor": {'silver': 1, 'herb(purification)': 1},
                "Surgeon's Needle": {'silver': 1, 'cloth': 1},
                'Repair Tools': {'iron': 3, 'wood(strong+durable)': 1},
                'Masterwork Tools': {'iron': 2, 'cloth': 1, 'wood(strong+durable)': 1},
                'Whetstone': {'stone': 4},
                'Throwing Snare': {'stone': 3, 'cloth': 3, 'soft pelt': 1},
                'Music Box': {'copper': 3, 'gold': 1, 'bone': 1, 'paper': 1},
                'Lasting': {'coal': 1, 'iron': 1, 'manganese': 1}}


crafted_item_lookup={
        "Animal Traps":{"iron":3},
        "Cooking Pot":{"copper":3,"wood (strong+durable)":1},
        "Gardener's Tools":{"iron":2,"wood (strong+durable)":1},
        "Mason's Chisel":{"iron":3,"wood (strong+durable)":1},
        "Surgeon's Razor":{"silver":1,"herb (purification)":1},
        "Surgeon's Needle":{"silver":1,"cloth":1},
        "Repair Tools":{"iron":3,"wood (strong+durable)":1},
        "Masterwork Tools":{"iron":2,"cloth":1,"wood (strong+durable)":1},
        "Whetstone":{"stone":4},
        "Throwing Snare":{"stone":3,"cloth":3,"soft pelt":1},
        "Music Box":{"copper":3,"gold":1,"bone":1,"paper":1},
        "Lasting":{"coal":1,"iron":1,"manganese":1},
        "Iron":{"iron":3},
        "Silver":{"silver":3,"sanctified water":1,"herb (purification)":3},
        "Gold":{"gold":3,"sanctified water":1,"herb (purification)":3},
        "Weapon-Casting":{"mercury":1,"silver":1,"herb (enhancement)":1},
        "Battering":{"coal":1,"stone":1,"iron":1,"marble":1,"manganese":1,"herb (enchantment)":2,"herb (enhancement)":2},
        "Massive":{"iron":4},
        "Ambidextrous":{"mercury":2,"salt":2},
        "Lasting":{"coal":1,"iron":1,"manganese":1},
        "Crushing":{"stone":3,"iron":2,"marble":2,"manganese":1,"demon blood":1,"herb (enchantment)":2,"herb (enhancement)":2,"herb (entropic)":4},
        "Elemental":{"coal":6,"mercury":2,"sulfur":2,"spell crystal":1,"herb (enhancement)":2,"herb (entropic)":3},
        "Sentinel":{"salt":1,"iron":1,"manganese":1,"soul gem":1,"celestial blood":1,"sanctified water":1,"herb (enhancement)":2,"herb (stimulant)":2},
        "Lethal":{"coal":2,"iron":2,"manganese":2},
        "Life-Drinking":{"obsidian":1,"soul gem":1,"demon blood":1,"zye blood parasite":2,"herb (entropic)":4,"herb (spiritual)":4},
        "Lasting":{"coal":1,"iron":1,"manganese":1},
        "Reinforced":{"coal":2,"iron":2,"manganese":2},
        "Spellcasting":{"quartz":1,"silver":1,"herb (enhancement)":1},
        "Spirit Protection":{"coal":1,"mercury":2,"silver":2,"sanctified water":1,"herb (purification)":1},
        "Glyph-Guarded":{"salt":1,"quartz":1,"ritual component":1,"herb (enhancement)":1},
        "Physically Resistant": {"coal":4, "iron":2, "manganese":2},
        "Wakethorn": {"obsidian":1, "bone":5, "herb (entropic)":3, "herb (stimulant)":3, "wood (flexible)":4},
        "Mindshatter": {"quartz":2, "silver":2, "fae blood":1, "herb (hallucination)":3},
        "Rageguard": {"mercury":3, "zye blood parasite":1, "herb (entropic)":3, "herb (stimulant)":3},
        "Deathward": {"gold":1, "feather":4, "celestial blood":2, "sanctified water":2, "herb (rejuvenation)":3},
        "Perfect Grip":{"iron":3,"soft pelt":1,"wood (flexible + durable)":1},
        "Spellcasting":{"quartz":1,"silver":1,"herb (enhancement)":1},
        "Savior":{"iron":1,"mercury":1,"manganese":1},
        "Lasting":{"coal":1,"iron":1,"manganese":1},
        "Unbreakable": {"salt":1, "quartz":1, "mercury":1, "ritual component":1, "herb (enhancement)":1},
        "Elemental Blocking": {"mercury":1, "sulfur":1, "herb (enhancement)":1, "wood (dense + durable + strong)":1},
        "Spell Reflecting": {"coal":1, "salt":1, "quartz":1, "copper":2, "manganese":1, "spell crystal":1, "herb (enhancement)":1},
        "Anchor-Weight": {"coal":4, "iron":2, "manganese":2},
        "Kinetic": {"salt":2, "sulfur":2, "obsidian":1, "wood (dense + flexible + strong)":2},
        "Mirroring": {"silver":2, "glass":2, "sanctified water":1, "herb (purification)":3, "wood (durable + dense + lightweight)":1},
        "Lock":{"coal":2,"iron":1,"manganese":1},
        "Keys":{"iron":1,"silver":1,"gold":1},
        "Lockpick":{"iron":1,"silver":1,"gold":1},
        "Explosive Key":{"Sulfur":2,"Glass":1,"Spell Crystal":1,"Herb (Entropic)":1},
        "Complex":{"Iron":1},
        "Iron Trap Mechanism":{"Iron":3,"Sulfur":1,"Herb (Entropic)":3},
        "Silver Trap Mechanism":{"Sulfur":1,"Silver":3,"Herb (Entropic)":3},
        "Gold Trap Mechanism":{"Sulfur":1,"Gold":3,"Herb (Entropic)":3},
        "Glyph-Guarded":{"Salt":1,"Quartz":1,"Mercury":1,"Ritual Component":1,"Herb (Enhancement)":1},
        "Secure Tome":{"Quartz":1,"Soft Pelt":1,"Herb (Enchantment)":2,"Herb (Spiritual)":2,"Wood (Durable)":1,"Paper":2},
        "Traveling Spellbook or Scroll Case":{"Quartz":1,"Bone":2,"Herb (Enchantment)":2,"Herb (Spiritual)":2,"Wood (Flexible + Lightweight)":1,"Paper":2},
        "Specialist’s Spellbook or Scroll Case":{"Quartz":1,"Bone":2,"Soft Pelt":1,"Herb (Enchantment)":2,"Herb (Spiritual)":2,"Wood (Flexible + Lightweight)":2,"Paper":2},
        "Master Spellbook or Scroll Case":{"Soul Gem":1,"Bone":2,"Soft Pelt":2,"Cloth":2,"Herb (Enchantment)":5,"Herb (Spiritual)":5,"Wood (Flexible + Lightweight)":3,"Paper":2},
        "Illuminating":{"Salt":3,"Quartz":1,"Glass":1,"Herb (Purification)":2,"Herb (Spiritual)":2},
        "Intuitive":{"Bone":1,"Demon Blood":1,"Herb (Hallucination)":1,"Herb (Purification)":1,"Any Spell Scroll":1},
        "Lasting":{"Coal":1,"Iron":1,"Manganese":1},
        "Geometer":{"Coal":2,"Stone":2,"Marble":2,"Obsidian":1,"Bone":2},
        "Poisoned Ring":{"Silver":2,"Bone":2,"Herb (Poisonous)":5},
        "Antidote Ring":{"Silver":2,"Mercury":1,"Herb (Enhancement)":1,"Herb (Entropy)":1,"Herb (Stimulant)":1},
        "Wakeful":{"Mercury":1,"Spell Crystal":1,"Feather":1,"Ritual Component":1,"Herb (Stimulant)":2},
        "Flowing":{"Copper":1,"Mercury":2,"Spell Crystal":1,"Ritual Component":1,"Herb (Enhancement)":1,"Herb (Entropic)":1,"Herb (Stimulant)":3},
        "Magically Resistant":{"Coal":1,"Salt":1,"Quartz":1,"Copper":2,"Manganese":1,"Spell Crystal":1,"Herb (Enhancement)":1},
        "Mind-Shielding":{"Mercury":2,"Gold":3,"Soft Pelt":1,"Celestial Blood":1,"Herb (Enhancement)":1,"Herb (Purification)":1},
        "Calm":{"Salt":1,"Mercury":1,"Sulfur":1,"Soul Gem":1,"Bone":3,"Demon Blood":2,"Ritual Component":1,"Herb (Sedative)":5},
        "Dichotomous":{"Demon Blood":1,"Celestial Blood":1,"Herb (Entropic)":3,"Herb (Healing)":3},
        "Passing":{"Feathers":3,"Glass":1,"Sanctified Water":1,"Herb (Enchantment)":3,"Herb (Purification)":3},
        "Arcane Detection":{"Salt":2,"Quartz":1,"Cloth":1,"Ritual Component":1,"Wood (Dense + Flexible)":2},
        "Lasting":{"Coal":1,"Iron":1,"Manganese":1},
        "Living":{"Soul Gem":1,"Bone":1,"Feathers":1,"Wood (Dense + Durable + Strong)":1,"Wood (Flexible + Lightweight)":1},
        "Detective":{"Quartz":2,"Silver":1,"Cloth":1,"Zye Scarab":1,"Herb (Hallucination)":3,"Herb (Spiritual)":3},
        "Power-Focus":{"Quartz":2,"Mercury":1,"Sulfur":1},
        "Healing":{"Bone":2,"Celestial Blood":2,"Sanctified Water":1,"Herb (Healing)":5,"Wood (Dense + Strong)":1},
        "Spell Reflecting":{"Quartz":1,"Spell Crystal":1,"Soft Pelt":1,"Ritual Component":1,"Wood (Lightweight)":1},
        "Dueling":{"Coal":1,"Salt":1,"Copper":2,"Manganese":1,"Spell Crystal":1,"Herb (Enhancement)":1},
        "Stitching":{"Sulfur":1,"Bone":1,"Demon Blood":1,"Child’s Tears":1,"Herb (Poisonous)":2,"Herb (Rejuvenation)":2},
        "Translucent":{"Mercury":1,"Spell Crystal":1,"Feathers":1,"Fae Blood":1,"Glass":1,"Ritual Component":1},
        "Free-Willed":{"Coal":1,"Quartz":1,"Obsidian":1,"Honey":2,"Celestial Blood":1,"Fae Blood":1,"Herb (Hallucination)":8},
        "Olive-Branch":{"Salt":1,"Marble":1,"Soul Gem":1,"Soft Pelt":1,"Demon Blood":1,"Cloth":1,"Zye Blood Parasite":1},
        "Lasting":{"Coal":1,"Iron":1,"Manganese":1},
        "Reinforced":{"Large Hide":2,"Cloth":2},
        "Spellcasting":{"Quartz":1,"Silver":1,"Herb (Enhancement)":1},
        "Disguise":{"Soft Pelt":2,"Cloth":2},
        "Spirit Protection":{"Mercury":1,"Silver":3,"Soft Pelt":1,"Sanctified Water":1,"Herb (Purification)":1},
        "Glyph-Guarded":{"Salt":1,"Quartz":1,"Mercury":1,"Ritual Component":1,"Herb (Enhancement)":1},
        "Physically Resistant":{"Honey":4,"Large Hide":2},
        "Wakethorn":{"Obsidian":1,"Bone":3,"Large Hide":1,"Herb (Entropic)":3,"Herb (Stimulant)":3},
        "Mindshatter":{"Quartz":1,"Silver":1,"Soft Pelt":1,"Fae Blood":1,"Herb (Hallucination)":3},
        "Rageguard":{"Mercury":2,"Zye Blood Parasite":1,"Herb (Entropic)":3,"Herb (Stimulant)":3},
        "Deathward":{"Gold":1,"Feather":3,"Celestial Blood":2,"Sanctified Water":1,"Herb (Rejuvenation)":3,"Herb (Spiritual)":3},
        "Bundle of Venom Arrows":{"Feathers":1,"Herb (Poisonous)":5},
        "Bundle of Messenger Arrows":{"Feathers":1,"Wood (Lightweight)":1},
        "Bundle of 'Bricks on Sticks'":{"Stone":1,"Wood (Dense)":1},
        "Bundle of Harpoon Arrows":{"Iron":1,"Wood (Durable)":1},
        "Bundle of Grappling Arrows":{"Feathers":1,"Wood (Strong)":1},
        "Bundle of Blessed Arrows":{"Feathers":1,"Sanctified Water":1},
        "Bundle of Marking Arrows":{"Zye Scarab":1,"Wood (Flexible)":1},
        "Iron Arrow":{"Iron":1,"Feathers":1,"Wood (Lightweight)":1},
        "Silver Arrow":{"Silver":1,"Feathers":1,"Sanctified Water":1,"Herb (Purification)":3,"Wood (Lightweight)":1},
        "Gold Arrow":{"Gold":1,"Feathers":1,"Sanctified Water":1,"Herb (Purification)":3,"Wood (Lightweight)":1},
        "Arrow-Casting":{"Mercury":1,"Silver":1,"Herb (Enhancement)":1},
        "Lasting":{"Coal":1,"Iron":1,"Manganese":1},
        "Elemental":{"Coal":2,"Mercury":2,"Sulfur":2,"Spell Crystal":1,"Feathers":1,"Herb (Enhancement)":2},
        "Life-Drinking":{"Obsidian":1,"Soul Gem":1,"Demon Blood":1,"Zye Blood Parasite":2,"Herb (Entropic)":4,"Herb (Spiritual)":4},
        "Lethal":{"Coal":2,"Iron":2,"Manganese":2},
        "Forge":{"coal":20,"stone":10,"iron":10},
        "Kitchen":{"coal":8,"salt":10,"stone":8,"iron":4,"marble":2,"herb (purification)":5,"wood (dense + durable)":8},
        "Shrine":{"stone":4,"sanctified water":1,"herb (purification)":3},
        "Work Table":{"iron":8,"large hide":3,"wood (dense + durable)":10},
        "Laboratory":{"coal":4,"salt":2,"copper":2,"marble":1,"mercury":3,"sulfur":6,"spell crystal":1,"herb (poisonous)":3,"herb (purification)":3},
        "Jail":{"Stone":20,"Iron":10},
        "Wooden Fortified Building":{"Iron":4,"Glass":1,"Wood (Durable)":15},
        "Library":{"Iron":2,"Feathers":3,"Paper":10,"Wood (Durable)":10},
        "Tavern":{"Stone":15,"Food (any variety)":8,"Glass":2,"Wood (any variety)":15},
        "Hideout":{"Iron":4,"Wood (Durable)":15},
        "Mobile Triage Tent":{"Large Hide":3,"Cloth":2,"Herb (Healing)":8,"Herb (Purification)":4,"Herb (Rejuvenation)":2,"Herb (Sedative)":2,"Herb (Stimulant)":4},
        "Ship":{"Workers":10,"Iron":2,"Cloth":6,"Wood (Durable)":10},
        "Alchemical Distillery":{"Quartz":2,"Copper":1,"Marble":2,"Glass":5,"Herb (Enchantment)":2,"Herb (Enhancement)":2,"Herb (Entropic)":2,"Herb (Hallucination)":2,"Herb (Healing)":2,"Herb (Poisonous)":2,"Herb (Purification)":2,"Herb (Sedative)":2,"Herb (Spiritual)":2,"Herb (Stimulant)":2,"Herb (Rejuvenation)":2,"Wood (Flexible)":5},
        "Healer's Tent":{"Large Hide":5,"Cloth":3,"Herb (Healing)":10,"Herb (Purification)":5,"Herb (Rejuvenation)":3,"Herb (Sedative)":3,"Herb (Stimulant)":5},
        "Stone Fortified Building":{"Wooden Fortified Building":1,"Stone":15,"Iron":6},
        "Soul of the Musician":{"Soul Gem":4,"Ritual Component":1,"Wood (Lightweight + Strong)":2,"Wood (Dense + Durable)":2},
        "Enhanced Furnace":{"Forge":1,"Coal":4,"Stone":1,"Iron":2,"Wood (Strong + Durable)":2},
        "Printing Press":{"Iron":2,"Paper":15,"Wood (Durable)":10},
        "Dungeon":{"Jail":1,"Stone":20,"Iron":10,"Herb (Healing)":5,"Herb (Poisonous)":5},
        "Warship":{"Ship":1,"Iron":6,"Manganese":2,"Cloth":4,"Wood (Strong)":4},
        "Cargo Ship":{"Ship":1,"Iron":3,"Cloth":4,"Wood (Dense)":4,"Wood (Strong)":4}
    }

item_lookup = {item: {**data, 'cat': cat} for cat, items in pivoted_items.items() for item, data in items.items()}

class NoAlternate(Exception):
    pass

class UnassignedItem(Exception):
    pass

class PointsExhausted(Exception):
    pass

class InsufficientPoints(Exception):
    pass

class OrderManager:
    def __init__(self,orders):
        self.pulls={ 
            'mercantile':[],
            'black_market':[],
            'hunting':[],
            'mining':[],
            'herbalism':[],
            'cargo_ship':[]}  # this will mutate so be careful- it is used to pass whatever the given orders are needed into other contexts

        for item in orders:
            try:
                pull_det=Pull(item.lower())
            except KeyError:
                continue
            if pull_det.is_herb is True:
                orders[item]=math.ceil(orders[item]/5) # herbs always come in sets of 5- therefore needing any between 1 and 5 is functionally identical. Dividing by 5 means if you need, say, 12, you get 3.
            for _ in range(orders[item]):
                self.pulls[pull_det.cat].append(pull_det)

        self.unassigned_pulls=[]
        
        self.eligible_alternates=[]
        self.cargo_pulls=[]
        self.overflow_pulls=[]

    def alternate_pulls(self):
        for pull in self.unassigned_pulls[:]:
            try:
                pull.alternate()
                self.eligible_alternates.append(pull)
                self.unassigned_pulls.remove(pull)
            except NoAlternate:
                continue
        self.build_dic(self.eligible_alternates)

    def set_sail(self):
        for pull in self.unassigned_pulls:
            if pull.cargo_ship is True:
                pull.cat='cargo_ship'
                self.cargo_pulls.append(pull)
            else:
                self.overflow_pulls.append(pull)
        self.unassigned_pulls=[]
        self.build_dic(self.cargo_pulls)

    def build_dic(self,list_):
        self.pulls={ 
            'mercantile':[],
            'black_market':[],
            'hunting':[],
            'mining':[],
            'herbalism':[],
            'cargo_ship':[]}
        for pull in list_:
            self.pulls[pull.cat].append(pull)

    def finalize(self):
        for pull in self.unassigned_pulls:
            self.overflow_pulls.append(pull)

    def call(self):
        return self.pulls

class Pull:
    def __init__(self,item):
        self.item=item.lower()
        try:
            dic_lookup=item_lookup[item]
        except KeyError:
            if 'herb' in self.item:
                self.parse_herb()
                return
            else:
                raise KeyError
        self.cost=dic_lookup['points']
        self.cat=dic_lookup['cat']
        if self.cost<=2 and self.cat=='mercantile':
            self.cargo_ship=True
        else:
            self.cargo_ship=False
        self.is_herb=False

    def parse_herb(self):
        self.cost=1 
        match=re.search(r'\((.*?)\)',self.item)
        if match:
            self.herb_type = match.group(1)
        self.cat='herbalism'
        self.cargo_ship=False
        self.is_herb=True

    def alternate(self):
        if self.item in alternates:
            new_cat=alternates[self.item]
            self.cat=new_cat
        else:
            raise NoAlternate

class AssignmentManager:
    def __init__(self,orders,employees_):
        self.employees_=employees_
        self.eligible_employees={
            'mercantile':employees_,
            'hunting':employees_,
            'black_market':employees_,
            'mining':employees_,
            'herbalism':employees_,
            'cargo_ship':employees_
        }
        
        self.assignment_made=False
        
        self.order_list=OrderManager(orders)
        
        self.pull_cat()

        self.order_list.alternate_pulls()

        self.pull_cat()

        self.order_list.set_sail()
        
        self.pull_cat()
        
        self.order_list.finalize()

    def pull_cat(self):
        for cat in self.order_list.pulls:
            order_list_=self.order_list.pulls[cat]
            for pull in order_list_:
                employees=self.eligible_employees[cat]
                try:
                    self.assign_pull(pull,employees)
                except UnassignedItem:
                    self.order_list.unassigned_pulls.append(pull)

    def assign_pull(self,pull,employees):
        for employee in employees[:]:
            try:
                self.check_eligibility(pull,employee)
                break
            except InsufficientPoints:
                continue

            except PointsExhausted:
                #self.eligible_employees[pull.cat].remove(employee)
                continue

        else:
            raise UnassignedItem    
    
    def check_eligibility(self,pull,employee):
        category=pull.cat
        current_score=employee.gathering_skills[category]
        if current_score>=pull.cost:
            self.assign_item(pull,employee)
        else:
            if current_score==0:
                raise PointsExhausted
            else:
                raise InsufficientPoints
    
    def assign_item(self,pull,employee):
        self.assignment_made=True
        category=pull.cat
        current_score=employee.gathering_skills[category]
        new_score=current_score-pull.cost
        employee.gathering_skills[category]=new_score
        if pull.is_herb is True:
            pull.item=pull.herb_type
        employee.assigned_pulls[category].append(pull.item)
        
class Assignments:
    def __init__(self, manager):
        self.manager=manager
        self.unpulled_items=[pull.item for pull in self.manager.order_list.overflow_pulls]
        self.no_pull_out=self.count_unassigned_items()
        self.all_pulls={emp.character_name: emp.assigned_pulls for emp in self.manager.employees_}

    def count_unassigned_items(self):
        self.unpulled_items=[pull.item for pull in self.manager.order_list.overflow_pulls]
        return Counter(self.unpulled_items)

class Person:
    def __init__(self,details):
        self.details=details
        self.uuid=details['uuid']
        self.character_name=details['character_name']
        self.player_name=details['player_name']
        self.discord=details['discord']
    
    def create(self,category=None):
        if category is None:
            raise AttributeError('No category defined.')
        self.uuid=str(uuid.uuid4())
        sql=f"SELECT MAX(ID) FROM {category}"
        cursor.execute(sql)
        max_id = cursor.fetchone()[0] or 0
        self.id=max_id+1
        self.day_created=date.today()

    def save(self):
        self.save_data=[self.uuid,self.id,self.character_name,self.player_name,self.day_created]

    def format(self):
        read_dic={'ID':self.id,'Character':self.character_name}
        return read_dic

class Employee(Person):
    def __init__(self,details):
        super().__init__(details)
        self.gathering_skills=details['gathering_skills']
        self.gathering_skills['cargo_ship']*=2
        self.rank=details['rank']
        self.assigned_pulls={
            'mining':[],
            'hunting':[],
            'mercantile':[],
            'black_market':[],
            'herbalism':[],
            'cargo_ship':[]
        }

    def save(self):
        super().save()
        self.save_data.append(self.rank)

    def format(self):
        read_dic=super().format()
        read_dic['Rank']=self.rank
        return read_dic

class PullingPlanner:
    def __init__(self,details,mats):
        self.details=details
        self.pulls=[]
        self.character=self.construct_character(self.details)
        orders=self.construct_orders(mats)
        self.assign_gathering(orders)
    
    def assign_gathering(self,orders, gathering=1):
        employee=copy.deepcopy(self.character)
        employee.character_name=gathering
        employees=[employee]
        ass_test=AssignmentManager(orders,employees)
        ass=Assignments(ass_test)
        
        if ass_test.assignment_made==True:
            self.pulls.append(ass.all_pulls)
            gathering+=1
            orders=dict(ass.no_pull_out)
            self.assign_gathering(orders,gathering)
        else:
            self.ineligible_pulls=ass.no_pull_out
    
    def construct_character(self,details):
        dets={
            'uuid':None,
            'rank':None,
            'discord':None,
            'character_name':details['character_name'],
            'player_name':None,
            'gathering_skills':details['gathering_skills']
        }
        emp=Employee(dets)
        return emp
        
    def construct_orders(self,desired_items):
        order_mats=[]
        for craft in desired_items:
            needed_mats=crafted_item_lookup[craft]
            for mat in needed_mats:
                for _ in range(needed_mats[mat]):
                    order_mats.append(mat)
        orders=dict(Counter(order_mats))
        return orders

@app.route("/select_items")
def select_items():
    return render_template("select_items.html")

@app.route("/submit_items", methods=["POST"])
def submit_items():
    selected_items = request.json.get("selected_items", [])
    # Instead of rendering, store in query params and redirect
    # (safer than trying to render with fetch)
    items_str = ",".join(selected_items)
    return {"redirect": url_for("set_gathering", items=items_str)}

@app.route("/set_gathering")
def set_gathering():
    items_param = request.args.get("items", "")
    selected_items = items_param.split(",") if items_param else []
    return render_template("set_gathering.html", selected_items=selected_items)

@app.route("/submit_gathering", methods=["POST"])
def submit_gathering():
    data = request.get_json()
    selected_items = data.get("selected_items", [])
    character_data = data.get("character_data", {})

    print(selected_items)
    print(character_data)

    ass = PullingPlanner(character_data, selected_items)

    pull_schedule = ass.pulls
    not_pulled = dict(ass.ineligible_pulls)

    print('skibbidi')
    
    return render_template("display_orders.html", pull_schedule=pull_schedule, not_pulled=not_pulled)

