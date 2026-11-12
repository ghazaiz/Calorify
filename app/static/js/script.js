document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;

    /* ===== Theme ===== */
    const themeToggle = document.querySelectorAll("[data-theme-toggle]");
    if (localStorage.getItem("calorify-theme") === "dark") {
        body.classList.add("dark-theme");
    }
    themeToggle.forEach((toggle) => {
        toggle.addEventListener("click", () => {
            const dark = body.classList.toggle("dark-theme");
            localStorage.setItem("calorify-theme", dark ? "dark" : "light");
        });
    });

    /* ===== Water tracker (persists per day in this browser) ===== */
    const WATER_GOAL = 2750;
    const waterKey = `calorify-water-${new Date().toISOString().slice(0, 10)}`;
    let water = 0;
    try { water = Number(localStorage.getItem(waterKey)) || 0; } catch (storageError) { /* private mode */ }

    const renderWater = () => {
        const total = document.querySelector("[data-water-total]");
        if (!total) return;
        total.textContent = water.toLocaleString();
        document.querySelector("[data-water-remaining]").textContent = Math.max(0, WATER_GOAL - water).toLocaleString();
        document.querySelector("[data-water-glasses]").textContent = Math.floor(water / 250);
        document.querySelector("[data-water-progress]").style.width = `${Math.min(100, (water / WATER_GOAL) * 100)}%`;
    };
    renderWater();

    document.querySelectorAll("[data-water]").forEach((button) => {
        button.addEventListener("click", () => {
            water = Math.min(WATER_GOAL, water + Number(button.dataset.water));
            try { localStorage.setItem(waterKey, water); } catch (storageError) { /* private mode */ }
            renderWater();
        });
    });

    /* ===== Meal modal (log / edit) ===== */
    const modal = document.querySelector("[data-meal-modal]");
    const form = document.querySelector("[data-meal-form]");
    const dialogTitle = document.querySelector("[data-meal-dialog-title]");
    let editingMealId = null;

    document.querySelectorAll("[data-open-meal]").forEach((button) => {
        button.addEventListener("click", () => {
            editingMealId = null;
            form?.reset();
            if (dialogTitle) dialogTitle.textContent = "Log a meal";
            modal.hidden = false;
        });
    });
    document.querySelector("[data-close-meal]")?.addEventListener("click", () => { modal.hidden = true; });
    modal?.addEventListener("click", (event) => { if (event.target === modal) modal.hidden = true; });

    document.querySelectorAll("[data-edit-meal]").forEach((button) => {
        button.addEventListener("click", () => {
            const meal = JSON.parse(button.dataset.editMeal);
            editingMealId = meal.meal_id;
            Object.entries(meal).forEach(([key, value]) => {
                const input = form.elements[key];
                if (input) input.value = value;
            });
            if (dialogTitle) dialogTitle.textContent = "Edit meal";
            modal.hidden = false;
        });
    });

    /* Live "after this meal" preview in the dashboard dialog */
    const mealFit = document.querySelector("[data-meal-fit]");
    form?.elements.calories?.addEventListener("input", () => {
        if (!mealFit) return;
        const goal = Number(mealFit.dataset.goal);
        const eaten = Number(mealFit.dataset.eaten);
        const calories = Number(form.elements.calories.value);
        if (!goal || !calories) { mealFit.hidden = true; return; }
        const left = goal - eaten - calories;
        mealFit.innerHTML = `AFTER THIS MEAL &nbsp; <b>${Math.abs(left)} kcal ${left >= 0 ? "left" : "over goal"}</b> · ${(eaten + calories).toLocaleString()} of ${goal.toLocaleString()}`;
        mealFit.hidden = false;
    });

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const error = form.querySelector("[data-meal-error]");
        const payload = Object.fromEntries(new FormData(form));
        ["quantity", "calories", "protein", "carbohydrates", "fats"].forEach((key) => { payload[key] = Number(payload[key]); });
        try {
            const endpoint = editingMealId ? `/meals/${editingMealId}` : "/meals/";
            const method = editingMealId ? "PUT" : "POST";
            const response = await fetch(endpoint, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
            if (!response.ok) throw new Error((await response.json()).message || "Unable to save meal");
            window.location.reload();
        } catch (requestError) {
            error.textContent = requestError.message;
        }
    });

    /* ===== Delete meal ===== */
    document.querySelectorAll("[data-delete-meal]").forEach((button) => {
        button.addEventListener("click", async () => {
            if (!window.confirm("Delete this meal?")) return;
            const response = await fetch(`/meals/${button.dataset.deleteMeal}`, { method: "DELETE" });
            if (response.ok) window.location.reload();
        });
    });

    /* ===== Add a saved meal to today ===== */
    document.querySelectorAll("[data-add-today]").forEach((button) => {
        button.addEventListener("click", async () => {
            const meal = JSON.parse(button.dataset.addToday);
            const payload = {
                food_name: meal.food_name,
                meal_type: meal.meal_type,
                quantity: meal.quantity,
                serving_unit: meal.serving_unit,
                calories: meal.calories,
                protein: meal.protein,
                carbohydrates: meal.carbohydrates,
                fats: meal.fats
            };
            const response = await fetch("/meals/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
            if (response.ok) {
                button.innerHTML = '<i class="bi bi-check2" aria-hidden="true"></i> Added to today';
                setTimeout(() => { button.innerHTML = '<i class="bi bi-plus-lg" aria-hidden="true"></i> Add to today'; }, 1800);
            }
        });
    });

    /* ===== My Meals search + filters ===== */
    const mealSearch = document.querySelector(".meal-toolbar input");
    mealSearch?.addEventListener("input", () => {
        const term = mealSearch.value.trim().toLowerCase();
        document.querySelectorAll(".saved-meal").forEach((card) => {
            card.hidden = term && !card.textContent.toLowerCase().includes(term);
        });
    });

    document.querySelectorAll("[data-filter-pills] button").forEach((pill) => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("[data-filter-pills] button").forEach((other) => other.classList.remove("active"));
            pill.classList.add("active");
            const type = pill.dataset.filter;
            document.querySelectorAll(".saved-meal").forEach((card) => {
                card.hidden = type !== "all" && card.dataset.mealType !== type;
            });
        });
    });

    /* ===== Food search: loading state while the lookup runs ===== */
    document.querySelectorAll("form.food-search").forEach((searchForm) => {
        searchForm.addEventListener("submit", () => {
            const button = searchForm.querySelector("button[type=submit]");
            if (button) {
                button.disabled = true;
                button.textContent = "Checking…";
                button.setAttribute("aria-busy", "true");
            }
        });
    });

    /* ===== Calorie check: quick picks ===== */
    document.querySelectorAll("[data-quick-picks] button").forEach((pick) => {
        pick.addEventListener("click", () => {
            const searchForm = document.querySelector("form.food-search");
            searchForm.querySelector("input[name=food]").value = pick.textContent.trim();
            searchForm.requestSubmit();
        });
    });

    /* ===== Calorie check: add result to today ===== */
    const checkResult = document.querySelector("[data-check-result]");
    document.querySelector("[data-add-check]")?.addEventListener("click", async () => {
        const errorBox = document.querySelector("[data-check-error]");
        const food = JSON.parse(checkResult.dataset.checkResult);
        const payload = {
            food_name: food.food_name,
            meal_type: document.querySelector("[data-add-meal-type]").value,
            quantity: food.quantity,
            serving_unit: food.serving_unit,
            calories: food.calories,
            protein: food.protein,
            carbohydrates: food.carbohydrates,
            fats: food.fats
        };
        try {
            const response = await fetch("/meals/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
            if (!response.ok) throw new Error((await response.json()).message || "Unable to add meal");
            window.location.href = "/reports/dashboard";
        } catch (requestError) {
            errorBox.textContent = requestError.message;
        }
    });

    /* ===== Calorie check: recent checks (saved in this browser) ===== */
    const recentList = document.querySelector("[data-recent-checks]");
    if (recentList) {
        const CHECKS_KEY = "calorify-recent-checks";
        const readChecks = () => {
            try { return JSON.parse(localStorage.getItem(CHECKS_KEY)) || []; } catch (storageError) { return []; }
        };
        const renderChecks = (checks) => {
            recentList.innerHTML = checks.length
                ? checks.map((check) => `<li><span class="check-time-icon"><i class="bi bi-clock-history" aria-hidden="true"></i></span><div>${check.name}<small>${check.when}</small></div><b>${check.calories} kcal</b></li>`).join("")
                : '<li class="muted">No checks yet.</li>';
        };

        let checks = readChecks();
        if (checkResult) {
            const food = JSON.parse(checkResult.dataset.checkResult);
            const today = new Date();
            checks.unshift({
                name: food.food_name,
                calories: Math.round(food.calories),
                when: `Today ${String(today.getHours()).padStart(2, "0")}:${String(today.getMinutes()).padStart(2, "0")}`
            });
            checks = checks.slice(0, 6);
            try { localStorage.setItem(CHECKS_KEY, JSON.stringify(checks)); } catch (storageError) { /* private mode */ }
        }
        renderChecks(checks);

        document.querySelector("[data-clear-checks]")?.addEventListener("click", () => {
            try { localStorage.removeItem(CHECKS_KEY); } catch (storageError) { /* private mode */ }
            renderChecks([]);
        });
    }

    /* ===== Guest mode: this-session checks ===== */
    const sessionList = document.querySelector("[data-session-checks]");
    if (sessionList) {
        const SESSION_KEY = "calorify-session-checks";
        let sessionChecks = [];
        try { sessionChecks = JSON.parse(sessionStorage.getItem(SESSION_KEY)) || []; } catch (storageError) { /* private mode */ }

        const guestResult = document.querySelector("[data-guest-result]");
        if (guestResult) {
            const food = JSON.parse(guestResult.dataset.guestResult);
            sessionChecks.unshift({ name: food.food_name, calories: food.calories });
            sessionChecks = sessionChecks.slice(0, 8);
            try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(sessionChecks)); } catch (storageError) { /* private mode */ }
        }

        if (sessionChecks.length) {
            sessionList.innerHTML = sessionChecks
                .map((check) => `<li><span class="check-time-icon"><i class="bi bi-search" aria-hidden="true"></i></span><div>${check.name}</div><b>${check.calories} kcal</b></li>`)
                .join("");
            const totalRow = document.querySelector("[data-session-total]");
            if (totalRow) {
                totalRow.hidden = false;
                totalRow.querySelector("b").textContent = `${sessionChecks.reduce((sum, check) => sum + check.calories, 0)} kcal`;
            }
        }
    }

    /* ===== Profile: password + delete dialogs ===== */
    const wireDialog = (openSelector, modalSelector, closeSelector) => {
        const dialog = document.querySelector(modalSelector);
        if (!dialog) return;
        document.querySelector(openSelector)?.addEventListener("click", () => { dialog.hidden = false; });
        document.querySelector(closeSelector)?.addEventListener("click", () => { dialog.hidden = true; });
        dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.hidden = true; });
    };
    wireDialog("[data-open-password]", "[data-password-modal]", "[data-close-password]");
    wireDialog("[data-open-delete]", "[data-delete-modal]", "[data-close-delete]");
});
