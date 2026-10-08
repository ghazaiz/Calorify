# Reusable ingredient nutrition values
# Values are approximate and represent nutrition per 100g.

INGREDIENTS = {
    "chicken": {
        "name": "Chicken",
        "calories_per_100g": 165,
        "protein_per_100g": 31,
        "carbohydrates_per_100g": 0,
        "fats_per_100g": 3.6
    },

    "beef": {
        "name": "Beef",
        "calories_per_100g": 250,
        "protein_per_100g": 26,
        "carbohydrates_per_100g": 0,
        "fats_per_100g": 15
    },

    "mutton": {
        "name": "Mutton",
        "calories_per_100g": 294,
        "protein_per_100g": 25,
        "carbohydrates_per_100g": 0,
        "fats_per_100g": 21
    }
}


# Desi food nutrition data
# Standard values are approximate because recipes vary.

DESI_FOODS = {

    # -------------------------
    # BREADS
    # -------------------------

    "roti": {
        "name": "Roti",
        "serving_size": 50,
        "serving_unit": "g",
        "calories": 130,
        "protein": 4,
        "carbohydrates": 27,
        "fats": 1
    },

    "naan": {
        "name": "Naan",
        "serving_size": 100,
        "serving_unit": "g",
        "calories": 260,
        "protein": 9,
        "carbohydrates": 50,
        "fats": 4
    },

    "paratha": {
        "name": "Paratha",
        "serving_size": 100,
        "serving_unit": "g",
        "calories": 320,
        "protein": 7,
        "carbohydrates": 45,
        "fats": 13
    },

    "aloo_paratha": {
        "name": "Aloo Paratha",
        "serving_size": 150,
        "serving_unit": "g",
        "calories": 350,
        "protein": 8,
        "carbohydrates": 50,
        "fats": 14
    },


    # -------------------------
    # BIRYANI
    # -------------------------

    "chicken_biryani": {
        "name": "Chicken Biryani",
        "serving_size": 300,
        "serving_unit": "g",

        # Base = rice, oil, spices, etc.
        "base_calories": 350,
        "base_protein": 8,
        "base_carbohydrates": 70,
        "base_fats": 6,

        "meat": "chicken"
    },

    "beef_biryani": {
        "name": "Beef Biryani",
        "serving_size": 300,
        "serving_unit": "g",

        "base_calories": 350,
        "base_protein": 8,
        "base_carbohydrates": 70,
        "base_fats": 6,

        "meat": "beef"
    },

    "mutton_biryani": {
        "name": "Mutton Biryani",
        "serving_size": 300,
        "serving_unit": "g",

        "base_calories": 350,
        "base_protein": 8,
        "base_carbohydrates": 70,
        "base_fats": 6,

        "meat": "mutton"
    },

    "vegetable_biryani": {
        "name": "Vegetable Biryani",
        "serving_size": 300,
        "serving_unit": "g",
        "calories": 500,
        "protein": 12,
        "carbohydrates": 78,
        "fats": 15
    },


    # -------------------------
    # KARAHI
    # -------------------------

    "chicken_karahi": {
        "name": "Chicken Karahi",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 450,
        "protein": 35,
        "carbohydrates": 12,
        "fats": 28
    },

    "beef_karahi": {
        "name": "Beef Karahi",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 520,
        "protein": 32,
        "carbohydrates": 12,
        "fats": 35
    },

    "mutton_karahi": {
        "name": "Mutton Karahi",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 550,
        "protein": 30,
        "carbohydrates": 12,
        "fats": 39
    },


    # -------------------------
    # CURRIES / SALAN
    # -------------------------

    "chicken_curry": {
        "name": "Chicken Curry",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 350,
        "protein": 30,
        "carbohydrates": 12,
        "fats": 20
    },

    "beef_curry": {
        "name": "Beef Curry",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 450,
        "protein": 30,
        "carbohydrates": 10,
        "fats": 30
    },

    "mutton_curry": {
        "name": "Mutton Curry",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 480,
        "protein": 28,
        "carbohydrates": 10,
        "fats": 34
    },

    "nihari": {
        "name": "Nihari",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 400,
        "protein": 28,
        "carbohydrates": 10,
        "fats": 28
    },

    "haleem": {
        "name": "Haleem",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 350,
        "protein": 20,
        "carbohydrates": 40,
        "fats": 12
    },


    # -------------------------
    # LENTILS / VEGETABLES
    # -------------------------

    "daal": {
        "name": "Daal",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 280,
        "protein": 16,
        "carbohydrates": 40,
        "fats": 6
    },

    "daal_chawal": {
        "name": "Daal Chawal",
        "serving_size": 350,
        "serving_unit": "g",
        "calories": 420,
        "protein": 16,
        "carbohydrates": 70,
        "fats": 8
    },

    "chana": {
        "name": "Chana",
        "serving_size": 200,
        "serving_unit": "g",
        "calories": 330,
        "protein": 18,
        "carbohydrates": 50,
        "fats": 7
    },

    "chana_chaat": {
        "name": "Chana Chaat",
        "serving_size": 200,
        "serving_unit": "g",
        "calories": 300,
        "protein": 14,
        "carbohydrates": 45,
        "fats": 7
    },

    "aloo_gosht": {
        "name": "Aloo Gosht",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 380,
        "protein": 25,
        "carbohydrates": 25,
        "fats": 20
    },

    "bhindi": {
        "name": "Bhindi",
        "serving_size": 200,
        "serving_unit": "g",
        "calories": 220,
        "protein": 5,
        "carbohydrates": 25,
        "fats": 11
    },


    # -------------------------
    # STREET FOOD
    # -------------------------

    "samosa": {
        "name": "Samosa",
        "serving_size": 80,
        "serving_unit": "g",
        "calories": 200,
        "protein": 5,
        "carbohydrates": 25,
        "fats": 9
    },

    "pakora": {
        "name": "Pakora",
        "serving_size": 100,
        "serving_unit": "g",
        "calories": 280,
        "protein": 6,
        "carbohydrates": 30,
        "fats": 15
    },

    "chicken_roll": {
        "name": "Chicken Roll",
        "serving_size": 180,
        "serving_unit": "g",
        "calories": 450,
        "protein": 22,
        "carbohydrates": 45,
        "fats": 20
    },

    "seekh_kebab": {
        "name": "Seekh Kebab",
        "serving_size": 100,
        "serving_unit": "g",
        "calories": 250,
        "protein": 20,
        "carbohydrates": 5,
        "fats": 17
    },

    "chicken_tikka": {
        "name": "Chicken Tikka",
        "serving_size": 150,
        "serving_unit": "g",
        "calories": 250,
        "protein": 38,
        "carbohydrates": 5,
        "fats": 9
    },


    # -------------------------
    # RICE
    # -------------------------

    "plain_rice": {
        "name": "Plain Rice",
        "serving_size": 200,
        "serving_unit": "g",
        "calories": 260,
        "protein": 5,
        "carbohydrates": 56,
        "fats": 1
    },

    "pulao": {
        "name": "Pulao",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 350,
        "protein": 8,
        "carbohydrates": 55,
        "fats": 10
    },


    # -------------------------
    # BREAKFAST
    # -------------------------

    "halwa_puri": {
        "name": "Halwa Puri",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 600,
        "protein": 10,
        "carbohydrates": 75,
        "fats": 28
    },

    "chana_puri": {
        "name": "Chana Puri",
        "serving_size": 250,
        "serving_unit": "g",
        "calories": 500,
        "protein": 14,
        "carbohydrates": 65,
        "fats": 20
    },

    "omelette": {
        "name": "Omelette",
        "serving_size": 100,
        "serving_unit": "g",
        "calories": 180,
        "protein": 12,
        "carbohydrates": 2,
        "fats": 13
    },


    # -------------------------
    # DAIRY / DRINKS
    # -------------------------

    "lassi": {
        "name": "Lassi",
        "serving_size": 250,
        "serving_unit": "ml",
        "calories": 150,
        "protein": 7,
        "carbohydrates": 18,
        "fats": 5
    },

    "sweet_lassi": {
        "name": "Sweet Lassi",
        "serving_size": 250,
        "serving_unit": "ml",
        "calories": 220,
        "protein": 6,
        "carbohydrates": 35,
        "fats": 6
    },

    "dahi": {
        "name": "Dahi",
        "serving_size": 200,
        "serving_unit": "g",
        "calories": 120,
        "protein": 7,
        "carbohydrates": 9,
        "fats": 6
    },


    # -------------------------
    # DESSERTS
    # -------------------------

    "kheer": {
        "name": "Kheer",
        "serving_size": 150,
        "serving_unit": "g",
        "calories": 220,
        "protein": 6,
        "carbohydrates": 32,
        "fats": 7
    },

    "gulab_jamun": {
        "name": "Gulab Jamun",
        "serving_size": 100,
        "serving_unit": "g",
        "calories": 300,
        "protein": 5,
        "carbohydrates": 45,
        "fats": 12
    },

    "gajar_halwa": {
        "name": "Gajar Halwa",
        "serving_size": 150,
        "serving_unit": "g",
        "calories": 250,
        "protein": 5,
        "carbohydrates": 35,
        "fats": 10
    }
}