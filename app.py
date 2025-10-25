from flask import Flask, render_template, request, jsonify, url_for
from collections import Counter
import copy

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
    'blood ink':'black_market'
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
            'cargo_ship':[]}  # this will mutate so be careful- it is used to pass whatever the given orders are needed into other contexts

        for item in orders:
            try:
                pull_det=Pull(item)
            except KeyError:
                continue
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
        self.item=item
        dic_lookup=item_lookup[item]
        self.cost=dic_lookup['points']
        self.cat=dic_lookup['cat']
        if self.cost<=2 and self.cat=='mercantile':
            self.cargo_ship=True
        else:
            self.cargo_ship=False

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

    ass = PullingPlanner(character_data, selected_items)

    pull_schedule = ass.pulls
    not_pulled = dict(ass.ineligible_pulls)

    print('skibbidi')
    
    return render_template("display_orders.html", pull_schedule=pull_schedule, not_pulled=not_pulled)

