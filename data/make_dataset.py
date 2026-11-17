"""
Builds the two CSV datasets used by the AI.

materials.csv    -> materials with real-world properties (used by the property model)
extra_names.csv  -> more everyday names + state (used only by the name model)

Run:  python data/make_dataset.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
S, L, G = "solid", "liquid", "gas"

# name, state, temp_c, melting_point_c, boiling_point_c, density_g_cm3, emoji, fun fact
# temp_c = the temperature where we normally meet the material (25 = room temperature)
# None = value not known / the material burns or breaks down instead of melting
ROWS = [
    # ---------------- SOLIDS ----------------
    ("stone", S, 25, 1200, None, 2.6, "🪨", "Stone is hard and keeps its shape."),
    ("rock", S, 25, 1200, None, 2.7, "🪨", "Mountains are made of rock."),
    ("wood", S, 25, None, None, 0.6, "🪵", "Wood comes from trees."),
    ("iron", S, 25, 1538, 2862, 7.87, "🔩", "Iron is a strong, heavy metal."),
    ("gold", S, 25, 1064, 2856, 19.3, "🥇", "Gold is shiny and very heavy."),
    ("silver", S, 25, 962, 2162, 10.5, "🥈", "Silver is a shiny metal used in jewellery."),
    ("copper", S, 25, 1085, 2562, 8.96, "🪙", "Electric wires are often made of copper."),
    ("aluminium", S, 25, 660, 2519, 2.7, "🥫", "Aluminium is light and used for cans and foil."),
    ("lead", S, 25, 327, 1749, 11.34, "", "Lead is a soft, heavy metal."),
    ("zinc", S, 25, 420, 907, 7.14, "", ""),
    ("tin", S, 25, 232, 2602, 7.3, "", ""),
    ("nickel", S, 25, 1455, 2913, 8.9, "", ""),
    ("steel", S, 25, 1450, None, 7.85, "🔧", "Steel is iron made even stronger."),
    ("brass", S, 25, 930, None, 8.5, "🔔", "Bells and keys are often made of brass."),
    ("diamond", S, 25, 3550, 4827, 3.5, "💎", "Diamond is the hardest natural solid."),
    ("coal", S, 25, None, None, 1.3, "⚫", "Coal is a black rock that burns."),
    ("salt", S, 25, 801, 1413, 2.16, "🧂", "Salt is made of tiny solid crystals."),
    ("sugar", S, 25, 186, None, 1.59, "🍬", "Sugar grains are tiny solids."),
    ("sand", S, 25, 1700, 2230, 1.6, "🏖️", "Sand pours like water but each grain is a solid."),
    ("chalk", S, 25, 825, None, 2.7, "🖍️", "Chalk is a soft solid we write with."),
    ("marble", S, 25, 825, None, 2.7, "", ""),
    ("glass", S, 25, 1400, None, 2.5, "🪟", "Glass is hard but can break."),
    ("brick", S, 25, 1000, None, 1.9, "🧱", "Houses are built with bricks."),
    ("cement", S, 25, None, None, 3.1, "", ""),
    ("concrete", S, 25, None, None, 2.4, "🏗️", "Concrete is a very hard building material."),
    ("clay", S, 25, None, None, 1.8, "🏺", "Clay is used to make pots."),
    ("ceramic", S, 25, 1600, None, 2.4, "", ""),
    ("paper", S, 25, None, None, 0.8, "📄", "Paper is made from wood."),
    ("cloth", S, 25, None, None, 1.5, "👕", "Clothes are made of cloth."),
    ("cotton", S, 25, None, None, 0.3, "🧶", "Cotton is soft and fluffy."),
    ("wool", S, 25, None, None, 1.3, "🧶", "Wool comes from sheep."),
    ("leather", S, 25, None, None, 0.9, "👜", ""),
    ("rubber", S, 25, None, None, 1.1, "⚽", "Rubber bounces back when you press it."),
    ("plastic", S, 25, 130, None, 1.0, "🧸", "Many toys are made of plastic."),
    ("bone", S, 25, None, None, 1.9, "🦴", ""),
    ("cork", S, 25, None, None, 0.24, "", "Cork is so light it floats."),
    ("sponge", S, 25, None, None, 0.05, "🧽", "A sponge is a solid you can squeeze."),
    ("bread", S, 25, None, None, 0.25, "🍞", ""),
    ("rice", S, 25, None, None, 0.85, "🍚", "Each grain of rice is a small solid."),
    ("flour", S, 25, None, None, 0.6, "🌾", ""),
    ("soap", S, 25, 50, None, 1.0, "🧼", ""),
    ("wax", S, 25, 55, 370, 0.9, "🕯️", "Candle wax is solid until it gets hot."),
    ("crayon", S, 25, 55, None, 0.95, "🖍️", ""),
    ("butter", S, 25, 32, None, 0.91, "🧈", "Butter melts if it is warm."),
    ("chocolate", S, 25, 34, None, 1.3, "🍫", "Chocolate melts in your hand!"),
    ("coin", S, 25, 1400, None, 8.0, "🪙", ""),
    ("key", S, 25, 930, None, 8.5, "🔑", ""),
    ("spoon", S, 25, 1450, None, 7.85, "🥄", ""),
    ("book", S, 25, None, None, 0.7, "📕", ""),
    ("pencil", S, 25, None, None, 0.7, "✏️", ""),
    ("eraser", S, 25, None, None, 1.2, "", ""),
    ("ice", S, -10, 0, 100, 0.92, "🧊", "Ice is water that has frozen solid."),
    ("ice cube", S, -5, 0, 100, 0.92, "🧊", "An ice cube melts into water."),
    ("snow", S, -5, 0, 100, 0.3, "❄️", "Snow is frozen water."),
    ("hail", S, -2, 0, 100, 0.9, "🌨️", "Hail falls as little balls of ice."),
    # ---------------- LIQUIDS ----------------
    ("water", L, 25, 0, 100, 1.0, "💧", "Water is the liquid we drink every day."),
    ("milk", L, 25, -0.5, 100, 1.03, "🥛", ""),
    ("juice", L, 25, -1, 100, 1.05, "🧃", ""),
    ("oil", L, 25, -10, 300, 0.92, "🫒", "Oil floats on water."),
    ("honey", L, 25, -10, 120, 1.42, "🍯", "Honey flows very slowly."),
    ("tea", L, 25, -0.5, 100, 1.0, "🍵", ""),
    ("coffee", L, 25, -0.5, 100, 1.0, "☕", ""),
    ("vinegar", L, 25, -2, 100, 1.01, "", ""),
    ("petrol", L, 25, -60, 150, 0.74, "⛽", "Petrol is a fuel for cars."),
    ("diesel", L, 25, -10, 300, 0.83, "⛽", ""),
    ("kerosene", L, 25, -30, 200, 0.8, "", ""),
    ("mercury", L, 25, -39, 357, 13.5, "🌡️", "Mercury is a metal that is a liquid!"),
    ("alcohol", L, 25, -114, 78, 0.79, "", ""),
    ("shampoo", L, 25, -2, 100, 1.02, "🧴", ""),
    ("ink", L, 25, 0, 100, 1.05, "🖋️", ""),
    ("blood", L, 25, -0.5, 100, 1.06, "🩸", ""),
    ("lemon juice", L, 25, -2, 100, 1.04, "🍋", ""),
    ("cold drink", L, 25, -1, 100, 1.04, "🥤", ""),
    ("sea water", L, 25, -2, 101, 1.025, "🌊", "Sea water is salty."),
    ("rain water", L, 25, 0, 100, 1.0, "🌧️", ""),
    ("syrup", L, 25, -5, 105, 1.3, "", ""),
    ("lemonade", L, 25, -1, 100, 1.03, "🍋", ""),
    ("liquid soap", L, 25, -2, 100, 1.05, "🧴", ""),
    ("bromine", L, 25, -7, 59, 3.1, "", ""),
    ("hand sanitizer", L, 25, -20, 80, 0.85, "🧴", ""),
    ("glycerine", L, 25, 18, 290, 1.26, "", ""),
    ("soup", L, 25, -1, 100, 1.03, "🍲", ""),
    ("perfume", L, 25, -90, 80, 0.85, "", ""),
    ("coconut water", L, 25, -1, 100, 1.02, "🥥", ""),
    ("hot tea", L, 70, -0.5, 100, 1.0, "🍵", "Hot tea is still a liquid."),
    ("hot milk", L, 70, -0.5, 100, 1.03, "🥛", ""),
    ("hot water", L, 60, 0, 100, 1.0, "♨️", ""),
    ("melted butter", L, 45, 32, None, 0.91, "🧈", "Warm butter turns into a liquid."),
    ("melted chocolate", L, 45, 34, None, 1.3, "🍫", ""),
    ("melted wax", L, 70, 55, 370, 0.9, "🕯️", "Hot wax is a liquid."),
    ("melted ice", L, 5, 0, 100, 1.0, "💧", "Melted ice is just water."),
    # ---------------- GASES ----------------
    ("air", G, 25, -213, -194, 0.0012, "🌬️", "Air is all around us."),
    ("oxygen", G, 25, -218, -183, 0.00143, "🫁", "We breathe in oxygen."),
    ("nitrogen", G, 25, -210, -196, 0.00125, "", "Most of the air is nitrogen."),
    ("hydrogen", G, 25, -259, -253, 0.00009, "", "Hydrogen is the lightest gas."),
    ("helium", G, 25, -272, -269, 0.00018, "🎈", "Helium makes balloons float."),
    ("carbon dioxide", G, 25, -78, -78, 0.00198, "🫧", "Fizzy drinks have carbon dioxide bubbles."),
    ("methane", G, 25, -182, -162, 0.00066, "", ""),
    ("lpg", G, 25, -188, -42, 0.002, "🔥", "LPG is the gas in a cooking cylinder."),
    ("neon", G, 25, -249, -246, 0.0009, "", ""),
    ("argon", G, 25, -189, -186, 0.00178, "", ""),
    ("chlorine", G, 25, -101, -34, 0.0032, "", ""),
    ("ammonia", G, 25, -78, -33, 0.00077, "", ""),
    ("natural gas", G, 25, -182, -162, 0.0008, "", ""),
    ("ozone", G, 25, -192, -112, 0.002, "", ""),
    ("laughing gas", G, 25, -91, -88, 0.0018, "", ""),
    ("propane", G, 25, -188, -42, 0.0019, "", ""),
    ("butane", G, 25, -138, -1, 0.0024, "", ""),
    ("carbon monoxide", G, 25, -205, -192, 0.0012, "", ""),
    ("sulphur dioxide", G, 25, -72, -10, 0.0027, "", ""),
    ("wind", G, 25, -213, -194, 0.0012, "💨", "Wind is moving air."),
    ("steam", G, 110, 0, 100, 0.0006, "♨️", "Steam is water that has boiled into a gas."),
    ("water vapour", G, 105, 0, 100, 0.0006, "☁️", "Water vapour is water as an invisible gas."),
    ("cooking gas", G, 25, -188, -42, 0.002, "🔥", ""),
    ("balloon gas", G, 25, -272, -269, 0.00018, "🎈", ""),
]

# (keeps_shape, flows, compressible) - the "things you can see and do" clues.
# Default: solid=(1,0,0)  liquid=(0,1,0)  gas=(0,0,1). These are the tricky exceptions.
DEFAULT_FLAGS = {S: (1, 0, 0), L: (0, 1, 0), G: (0, 0, 1)}
EXCEPTIONS = {
    "sand": (1, 1, 0), "salt": (1, 1, 0), "sugar": (1, 1, 0), "rice": (1, 1, 0), "flour": (1, 1, 0),
    "sponge": (1, 0, 1), "cotton": (1, 0, 1), "wool": (1, 0, 1), "bread": (1, 0, 1), "snow": (1, 0, 1),
}

# More everyday names for the *name model* only (no property values).
EXTRA = {
    S: "iron nail,steel plate,gold ring,silver coin,copper wire,wooden table,wooden stick,pebble,"
       "brick wall,glass bottle,plastic bottle,rubber ball,paper plate,notebook,pencil box,school bag,"
       "toy block,candy,biscuit,cookie,apple,banana,carrot,potato,wooden door,steel spoon,iron box,"
       "plastic toy,chalk piece,tile,towel,shirt,shoe,tyre,table,chair,bed,hammer,scissors,bat,ruler,"
       "stick,rope,bag,box,ball,toy car,cake,bread slice,mud brick,ice block,frozen water,"
       "iceberg,glacier,icicle,metal,stone wall,cup,plate,bucket,window glass,diamond ring",
    L: "orange juice,apple juice,mango juice,cold coffee,green tea,black tea,rose water,soda water,"
       "mineral water,drinking water,river water,tap water,lake water,salt water,sugar water,baby oil,"
       "olive oil,mustard oil,coconut oil,sunflower oil,engine oil,hair oil,lemon water,buttermilk,"
       "cow milk,almond milk,hand wash,dish wash liquid,paint,nail polish,medicine syrup,cough syrup,"
       "tomato juice,fruit juice,sugarcane juice,tender coconut water,body lotion,liquid,rain,dew,"
       "tears,sweat,saliva,gasoline,fuel,spirit,acid,milkshake,smoothie,broth,gravy,sauce,"
       "melted ice cream,boiled water,warm water,cold water,ice water",
    G: "oxygen gas,nitrogen gas,hydrogen gas,helium gas,carbon dioxide gas,lpg gas,steam from kettle,"
       "fresh air,cold air,hot air,breath air,marsh gas,neon gas,chlorine gas,ammonia gas,methane gas,"
       "gas,vapour,vapor,fumes,gas cylinder,air in balloon,air in tyre,boiling water steam,"
       "kitchen steam,cooking steam,hot steam,bio gas,gobar gas,exhaust gas,smell gas,gas stove gas",
}


def check_physics(name, state, temp, mp, bp):
    """Data-quality check: the label must agree with real physics when we know mp / bp."""
    expected = None
    if mp is not None and temp < mp:
        expected = S
    elif bp is not None and temp >= bp:
        expected = G
    elif mp is not None and temp >= mp:
        expected = L
    if expected is not None:
        assert expected == state, f"Label problem for {name}: {state} vs physics {expected}"


def main():
    seen = set()
    with open(HERE / "materials.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["material", "state", "temp_c", "melting_point_c", "boiling_point_c",
                    "density_g_cm3", "keeps_shape", "flows", "compressible", "emoji", "fact"])
        for name, state, temp, mp, bp, dens, emoji, fact in ROWS:
            assert name not in seen, f"duplicate {name}"
            seen.add(name)
            check_physics(name, state, temp, mp, bp)
            ks, fl, co = EXCEPTIONS.get(name, DEFAULT_FLAGS[state])
            w.writerow([name, state, temp, "" if mp is None else mp, "" if bp is None else bp,
                        dens, ks, fl, co, emoji, fact])
    n_extra = 0
    with open(HERE / "extra_names.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["material", "state"])
        for state, names in EXTRA.items():
            for n in names.split(","):
                n = n.strip()
                if n and n not in seen:
                    seen.add(n)
                    w.writerow([n, state])
                    n_extra += 1
    print(f"materials.csv: {len(ROWS)} rows | extra_names.csv: {n_extra} rows")


if __name__ == "__main__":
    main()
