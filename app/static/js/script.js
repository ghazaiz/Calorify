document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const themeToggle = document.querySelector("[data-theme-toggle]");
    const savedTheme = localStorage.getItem("calorify-theme");
    if (savedTheme === "dark") {
        body.classList.add("dark-theme");
        if (themeToggle) themeToggle.textContent = "Light theme";
    }
    themeToggle?.addEventListener("click", () => {
        const dark = body.classList.toggle("dark-theme");
        localStorage.setItem("calorify-theme", dark ? "dark" : "light");
        themeToggle.textContent = dark ? "Light theme" : "Dark theme";
    });

    let water = 0;
    document.querySelectorAll("[data-water]").forEach((button) => {
        button.addEventListener("click", () => {
            water = Math.min(2750, water + Number(button.dataset.water));
            document.querySelector("[data-water-total]").textContent = water.toLocaleString();
            document.querySelector("[data-water-remaining]").textContent = (2750 - water).toLocaleString();
            document.querySelector("[data-water-glasses]").textContent = Math.floor(water / 250);
            document.querySelector("[data-water-progress]").style.width = `${water / 27.5}%`;
        });
    });

    const modal = document.querySelector("[data-meal-modal]");
    const form = document.querySelector("[data-meal-form]");
    let editingMealId = null;
    document.querySelector("[data-open-meal]")?.addEventListener("click", () => { modal.hidden = false; });
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
            modal.hidden = false;
        });
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

    document.querySelectorAll("[data-delete-meal]").forEach((button) => {
        button.addEventListener("click", async () => {
            if (!window.confirm("Delete this meal?")) return;
            const response = await fetch(`/meals/${button.dataset.deleteMeal}`, { method: "DELETE" });
            if (response.ok) window.location.reload();
        });
    });
});