document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const roundNutrition = (value) => Math.floor(value * 100 + 0.5) / 100;
    const svgNamespace = "http://www.w3.org/2000/svg";
    const makeIcon = (name) => {
        const svg = document.createElementNS(svgNamespace, "svg");
        const use = document.createElementNS(svgNamespace, "use");
        svg.setAttribute("class", "app-icon");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("focusable", "false");
        use.setAttribute("href", `${body.dataset.iconSprite}#${name}`);
        svg.append(use);
        return svg;
    };

    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const password = document.getElementById(button.getAttribute("aria-controls"));
        button.addEventListener("click", () => {
            const visible = password.type === "password";
            password.type = visible ? "text" : "password";
            button.textContent = visible ? "Hide" : "Show";
            button.setAttribute("aria-pressed", String(visible));
        });
    });

    /* ===== Theme ===== */
    const themeToggle = document.querySelectorAll("[data-theme-toggle]");
    try {
        if (localStorage.getItem("calorify-theme") === "dark") body.classList.add("dark-theme");
    } catch (storageError) { /* storage unavailable */ }
    const syncThemeToggles = () => {
        const dark = body.classList.contains("dark-theme");
        themeToggle.forEach((toggle) => toggle.setAttribute("aria-pressed", String(dark)));
    };
    syncThemeToggles();
    themeToggle.forEach((toggle) => {
        toggle.addEventListener("click", () => {
            const dark = body.classList.toggle("dark-theme");
            syncThemeToggles();
            try { localStorage.setItem("calorify-theme", dark ? "dark" : "light"); } catch (storageError) { /* storage unavailable */ }
        });
    });

    const dialogOpeners = new WeakMap();
    const showDialog = (dialog, opener, initialFocus) => {
        dialogOpeners.set(dialog, opener);
        dialog.hidden = false;
        body.classList.add("dialog-open");
        initialFocus.focus();
    };
    const hideDialog = (dialog) => {
        dialog.hidden = true;
        body.classList.remove("dialog-open");
        dialogOpeners.get(dialog)?.focus();
    };
    document.addEventListener("keydown", (event) => {
        const dialog = document.querySelector(".meal-modal:not([hidden])");
        if (!dialog) return;
        if (event.key === "Escape") {
            event.preventDefault();
            hideDialog(dialog);
        }
        if (event.key === "Tab") {
            const focusables = [...dialog.querySelectorAll("button, input, select, textarea, a[href]")]
                .filter((element) => !element.disabled && element.tabIndex >= 0 && element.getClientRects().length);
            const edge = event.shiftKey ? focusables[0] : focusables.at(-1);
            if (document.activeElement === edge || !dialog.contains(document.activeElement)) {
                event.preventDefault();
                (event.shiftKey ? focusables.at(-1) : focusables[0])?.focus();
            }
        }
    });

    /* ===== Water tracker (persists per day in this browser) ===== */
    const WATER_GOAL = 2750;
    const waterDate = new Date();
    const localDate = [
        waterDate.getFullYear(),
        String(waterDate.getMonth() + 1).padStart(2, "0"),
        String(waterDate.getDate()).padStart(2, "0")
    ].join("-");
    const waterKey = `calorify-water-${localDate}`;
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

    const saveMeal = async (endpoint, method, payload) => {
        let response;
        try {
            response = await fetch(endpoint, {
                method,
                headers: { "Content-Type": "application/json", "Accept": "application/json" },
                body: payload ? JSON.stringify(payload) : undefined,
                redirect: "error"
            });
        } catch (error) {
            throw new Error("Could not reach the meal service. Check your connection or sign in again.");
        }
        const result = await response.json().catch(() => null);
        if (!response.ok || !result) {
            throw new Error(result?.message || "The meal could not be saved. Try again.");
        }
        return result;
    };

    /* ===== Meal modal (log / edit) ===== */
    const modal = document.querySelector("[data-meal-modal]");
    const form = document.querySelector("[data-meal-form]");
    const dialogTitle = document.querySelector("[data-meal-dialog-title]");
    let editingMealId = null;
    let originalMeal = null;
    const mealFields = ["calories", "protein", "carbohydrates", "fats"];
    const resizeStatus = form?.querySelector("[data-resize-status]");
    const scaleEditableMeal = () => {
        const amount = form.elements.quantity.valueAsNumber;
        if (!originalMeal || !Number.isFinite(amount) || amount <= 0) return;
        if (form.elements.serving_unit.value !== originalMeal.serving_unit) {
            resizeStatus.textContent = "Check the nutrition totals for the new unit.";
            return;
        }
        const factor = amount / originalMeal.quantity;
        mealFields.forEach((key) => {
            form.elements[key].value = roundNutrition(originalMeal[key] * factor);
        });
        resizeStatus.textContent = "Nutrition scaled to the new amount. You can adjust the totals.";
        redrawMealFit();
    };
    form?.elements.quantity?.addEventListener("input", scaleEditableMeal);
    form?.elements.serving_unit?.addEventListener("change", () => {
        if (originalMeal) resizeStatus.textContent = "Check the nutrition totals for the selected unit.";
    });
    mealFields.forEach((key) => {
        form?.elements[key]?.addEventListener("change", () => {
            if (!originalMeal) return;
            const amount = form.elements.quantity.valueAsNumber;
            if (Number.isFinite(amount) && amount > 0 && form.elements.serving_unit.value === originalMeal.serving_unit) {
                const factor = originalMeal.quantity / amount;
                originalMeal[key] = form.elements[key].valueAsNumber * factor;
            }
        });
    });

    document.querySelectorAll("[data-open-meal]").forEach((button) => {
        button.addEventListener("click", () => {
            editingMealId = null;
            originalMeal = null;
            form?.reset();
            form?.querySelector("[data-meal-error]").replaceChildren();
            resizeStatus.textContent = "";
            redrawMealFit();
            if (dialogTitle) dialogTitle.textContent = "Log a meal";
            showDialog(modal, button, form.elements.food_name);
        });
    });
    document.querySelector("[data-close-meal]")?.addEventListener("click", () => hideDialog(modal));
    modal?.addEventListener("click", (event) => { if (event.target === modal) hideDialog(modal); });

    document.querySelectorAll("[data-edit-meal]").forEach((button) => {
        button.addEventListener("click", () => {
            const meal = JSON.parse(button.dataset.editMeal);
            editingMealId = meal.meal_id;
            originalMeal = { ...meal };
            form.querySelector("[data-meal-error]").replaceChildren();
            Object.entries(meal).forEach(([key, value]) => {
                const input = form.elements[key];
                if (input) input.value = value;
            });
            resizeStatus.textContent = "";
            if (dialogTitle) dialogTitle.textContent = "Edit meal";
            showDialog(modal, button, form.elements.food_name);
        });
    });

    /* Live "after this meal" preview in the dashboard dialog */
    const mealFit = document.querySelector("[data-meal-fit]");
    const redrawMealFit = () => {
        if (!mealFit) return;
        const goal = Number(mealFit.dataset.goal);
        const eaten = Number(mealFit.dataset.eaten);
        const calories = Number(form.elements.calories.value);
        if (!goal || !calories) { mealFit.hidden = true; return; }
        const left = goal - eaten - calories;
        mealFit.innerHTML = `AFTER THIS MEAL &nbsp; <b>${Math.abs(left)} kcal ${left >= 0 ? "left" : "over goal"}</b> · ${(eaten + calories).toLocaleString()} of ${goal.toLocaleString()}`;
        mealFit.hidden = false;
    };
    form?.elements.calories?.addEventListener("input", redrawMealFit);

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const error = form.querySelector("[data-meal-error]");
        const button = form.querySelector("[type=submit]");
        if (button.disabled) return;
        error.textContent = "";
        button.disabled = true;
        button.textContent = "Saving…";
        const payload = Object.fromEntries(new FormData(form));
        ["quantity", ...mealFields].forEach((key) => { payload[key] = Number(payload[key]); });
        try {
            const endpoint = editingMealId ? `/meals/${editingMealId}` : "/meals/";
            await saveMeal(endpoint, editingMealId ? "PUT" : "POST", payload);
            window.location.assign(`${window.location.pathname}?meal_saved=1`);
        } catch (requestError) {
            error.textContent = requestError.message;
            button.disabled = false;
            button.textContent = "Save meal";
        }
    });

    /* ===== Delete meal ===== */
    document.querySelectorAll("[data-delete-meal]").forEach((button) => {
        button.addEventListener("click", async () => {
            if (!window.confirm("Delete this meal?")) return;
            button.disabled = true;
            const status = document.querySelector("[data-meals-status]");
            try {
                await saveMeal(`/meals/${button.dataset.deleteMeal}`, "DELETE");
                window.location.assign("/meals/?meal_deleted=1");
            } catch (error) {
                status.textContent = error.message;
                button.disabled = false;
            }
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
            button.disabled = true;
            const status = document.querySelector("[data-meals-status]");
            try {
                await saveMeal("/meals/", "POST", payload);
                window.location.assign("/meals/?meal_saved=1");
            } catch (error) {
                status.textContent = error.message;
                button.disabled = false;
            }
        });
    });

    /* ===== My Meals search + filters ===== */
    const mealSearch = document.querySelector(".meal-toolbar input");
    const filterPills = document.querySelectorAll("[data-filter-pills] button");
    const mealCards = Array.from(document.querySelectorAll(".saved-meal"), (card) => ({
        card,
        text: card.textContent.toLowerCase(),
        type: card.dataset.mealType
    }));
    let mealType = "all";
    const filterMeals = () => {
        const term = mealSearch?.value.trim().toLowerCase() || "";
        let visible = 0;
        mealCards.forEach(({ card, text, type }) => {
            card.hidden = !text.includes(term) || (mealType !== "all" && type !== mealType);
            if (!card.hidden) visible += 1;
        });
        const empty = document.querySelector("[data-meals-filter-empty]");
        if (empty) empty.hidden = visible !== 0;
    };
    mealSearch?.addEventListener("input", filterMeals);

    filterPills.forEach((pill) => {
        pill.addEventListener("click", () => {
            filterPills.forEach((other) => {
                other.classList.toggle("active", other === pill);
                other.setAttribute("aria-pressed", String(other === pill));
            });
            mealType = pill.dataset.filter;
            filterMeals();
        });
    });

    /* ===== Food search: loading state while the lookup runs ===== */
    document.querySelectorAll("form.food-search").forEach((searchForm) => {
        const button = searchForm.querySelector("button[type=submit]");
        const label = button.querySelector("span");
        const idleLabel = label.textContent;
        searchForm.addEventListener("invalid", (event) => {
            const details = event.target.closest("details");
            if (details && searchForm.contains(details)) details.open = true;
        }, true);
        searchForm.addEventListener("submit", () => {
            button.disabled = true;
            label.textContent = idleLabel === "Calculate" ? "Calculating…" : "Searching…";
            button.setAttribute("aria-busy", "true");
        });
        window.addEventListener("pageshow", () => {
            button.disabled = false;
            label.textContent = idleLabel;
            button.removeAttribute("aria-busy");
        });
    });

    /* ===== Calorie check: quick picks ===== */
    const measuredFood = document.querySelector(".food-search input[name=food]");
    const biryaniPortion = document.querySelector("[data-biryani-portion]");
    const updateBiryaniPortion = () => {
        const isBiryani = /\b(?:biryani|biriyani|briyani)\b/i.test(measuredFood.value);
        biryaniPortion.hidden = !isBiryani;
        if (!isBiryani) biryaniPortion.open = false;
        biryaniPortion.querySelectorAll("input, select").forEach((field) => {
            field.disabled = !isBiryani;
        });
    };
    if (measuredFood && biryaniPortion) {
        measuredFood.addEventListener("input", updateBiryaniPortion);
        updateBiryaniPortion();
    }
    document.querySelectorAll("[data-quick-picks] button").forEach((pick) => {
        pick.addEventListener("click", () => {
            const searchForm = document.querySelector("form.food-search");
            searchForm.reset();
            searchForm.querySelector("input[name=quantity]").value = "";
            searchForm.querySelector("input[name=meat_weight]").value = "";
            searchForm.querySelector("select[name=unit]").value = "g";
            searchForm.querySelector("input[name=food]").value = pick.textContent.trim();
            updateBiryaniPortion();
            searchForm.requestSubmit();
        });
    });

    /* ===== Nutrition portions and meal logging ===== */
    const resultCard = document.querySelector("[data-nutrition-result]");
    if (resultCard) {
        const reference = JSON.parse(resultCard.dataset.reference);
        const units = JSON.parse(resultCard.dataset.units);
        const amount = resultCard.querySelector("[data-portion-amount]");
        const unit = resultCard.querySelector("[data-portion-unit]");
        const basis = resultCard.querySelector("[data-portion-basis]");
        const portionError = resultCard.querySelector("[data-portion-error]");
        const goalPreview = resultCard.querySelector("[data-goal-preview]");
        const logButton = resultCard.querySelector("[data-add-check]");
        const nutrientFields = resultCard.querySelectorAll("[data-nutrient]");
        let confirmed = resultCard.dataset.portionUnavailable !== "true";
        let payload;

        const updatePortion = () => {
            const quantity = amount.valueAsNumber;
            const basisAmount = quantity * units[unit.value];
            const valid = amount.validity.valid && Number.isFinite(basisAmount)
                && basisAmount > 0 && basisAmount <= Number(amount.max);
            const factor = basisAmount / reference.serving_size;

            payload = valid && confirmed ? {
                food_name: reference.name,
                quantity,
                serving_unit: unit.value,
            } : null;
            nutrientFields.forEach((field) => {
                const key = field.dataset.nutrient;
                const value = reference[key];
                const scaled = valid && typeof value === "number" ? roundNutrition(value * factor) : null;
                field.textContent = scaled ?? "?";
                if (payload) payload[key] = scaled;
            });

            basis.textContent = valid ? `${roundNutrition(basisAmount)} ${reference.serving_unit} total` : "";
            portionError.textContent = valid
                ? (confirmed ? "" : "Adjust the amount or unit to confirm this reference portion.")
                : `Enter a total between 0 and ${Number(amount.max).toLocaleString()} ${reference.serving_unit}.`;
            if (logButton) logButton.disabled = !payload || logButton.dataset.saving === "true";

            if (goalPreview && payload) {
                const remaining = Number(goalPreview.dataset.goal)
                    - Number(goalPreview.dataset.eaten) - payload.calories;
                const status = remaining >= 0 ? "left after this meal" : "over your daily goal after this meal";
                goalPreview.textContent = `${roundNutrition(Math.abs(remaining))} kcal ${status}`;
            } else if (goalPreview) {
                goalPreview.textContent = "";
            }
        };

        const confirmPortion = () => {
            confirmed = true;
            updatePortion();
        };
        amount.addEventListener("input", confirmPortion);
        unit.addEventListener("change", confirmPortion);
        updatePortion();

        logButton?.addEventListener("click", async () => {
            if (!payload || logButton.disabled) return;
            const errorBox = resultCard.querySelector("[data-check-error]");
            errorBox.textContent = "";
            logButton.dataset.saving = "true";
            logButton.disabled = true;
            logButton.textContent = "Logging?";
            try {
                await saveMeal("/meals/", "POST", {
                    ...payload,
                    meal_type: resultCard.querySelector("[data-add-meal-type]").value,
                });
                window.location.assign("/reports/dashboard?meal_saved=1");
            } catch (error) {
                errorBox.textContent = error.message;
                logButton.dataset.saving = "false";
                logButton.textContent = "Log meal";
                updatePortion();
            }
        });
    }

    const checkListItem = (check, iconName) => {
        const item = document.createElement("li");
        const iconWrapper = document.createElement("span");
        iconWrapper.classList.add("check-time-icon");
        iconWrapper.append(makeIcon(iconName));
        const description = document.createElement("div");
        description.textContent = check.name;
        if (check.when) {
            const time = document.createElement("small");
            time.textContent = check.when;
            description.append(time);
        }
        const calories = document.createElement("b");
        calories.textContent = `${check.calories} kcal`;
        item.append(iconWrapper, description, calories);
        return item;
    };

    const readChecks = (storage, key) => {
        try {
            const checks = JSON.parse(window[storage].getItem(key));
            return Array.isArray(checks)
                ? checks.filter((check) => typeof check?.name === "string" && Number.isFinite(check.calories))
                : [];
        } catch (storageError) {
            return [];
        }
    };

    /* ===== Calorie check: recent checks (saved in this browser) ===== */
    const recentList = document.querySelector("[data-recent-checks]");
    if (recentList) {
        const CHECKS_KEY = "calorify-recent-checks";
        const renderChecks = (checks) => {
            if (checks.length) {
                recentList.replaceChildren(...checks.map((check) => checkListItem(check, "history")));
            } else {
                const empty = document.createElement("li");
                empty.classList.add("muted");
                empty.textContent = "No checks yet.";
                recentList.replaceChildren(empty);
            }
        };

        let checks = readChecks("localStorage", CHECKS_KEY);
        if (resultCard?.dataset.checkResult) {
            const food = JSON.parse(resultCard.dataset.checkResult);
            const when = new Date().toLocaleString([], {
                month: "short", day: "numeric", hour: "numeric", minute: "2-digit"
            });
            checks = checks.filter((check) => check.name !== food.food_name || check.calories !== food.calories);
            checks.unshift({ name: food.food_name, calories: food.calories, when });
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
        let sessionChecks = readChecks("sessionStorage", SESSION_KEY);

        const guestResult = document.querySelector("[data-guest-result]");
        if (guestResult) {
            const food = JSON.parse(guestResult.dataset.guestResult);
            sessionChecks = sessionChecks.filter((check) => check.name !== food.food_name || check.calories !== food.calories);
            sessionChecks.unshift({ name: food.food_name, calories: food.calories });
            sessionChecks = sessionChecks.slice(0, 8);
            try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(sessionChecks)); } catch (storageError) { /* private mode */ }
        }

        if (sessionChecks.length) {
            sessionList.replaceChildren(...sessionChecks.map((check) => checkListItem(check, "search")));
            const totalRow = document.querySelector("[data-session-total]");
            if (totalRow) {
                totalRow.hidden = false;
                totalRow.querySelector("b").textContent = `${roundNutrition(sessionChecks.reduce((sum, check) => sum + check.calories, 0))} kcal`;
            }
        }
    }

    /* ===== Profile: password + delete dialogs ===== */
    const wireDialog = (openSelector, modalSelector, closeSelector) => {
        const dialog = document.querySelector(modalSelector);
        if (!dialog) return;
        const opener = document.querySelector(openSelector);
        const close = dialog.querySelector(closeSelector);
        const initialFocus = dialog.querySelector("input") || close;
        opener?.addEventListener("click", () => showDialog(dialog, opener, initialFocus));
        close.addEventListener("click", () => hideDialog(dialog));
        dialog.addEventListener("click", (event) => { if (event.target === dialog) hideDialog(dialog); });
        if (!dialog.hidden) showDialog(dialog, opener, initialFocus);
    };
    wireDialog("[data-open-password]", "[data-password-modal]", "[data-close-password]");
    wireDialog("[data-open-delete]", "[data-delete-modal]", "[data-close-delete]");
});
