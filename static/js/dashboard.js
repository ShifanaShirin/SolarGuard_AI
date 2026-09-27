document.addEventListener("DOMContentLoaded", function () {

    const searchBox = document.getElementById("panelSearch");

    // Exit if search box doesn't exist on this page
    if (!searchBox) {
        return;
    }

    searchBox.addEventListener("keyup", function () {

        const keyword = this.value.toLowerCase();

        const rows = document.querySelectorAll("#panelTable tr");

        rows.forEach(function (row) {

            const name = row.dataset.name || "";
            const manufacturer = row.dataset.manufacturer || "";
            const location = row.dataset.location || "";
            const serial = row.dataset.serial || "";

            if (
                name.includes(keyword) ||
                manufacturer.includes(keyword) ||
                location.includes(keyword) ||
                serial.includes(keyword)
            ) {

                row.style.display = "";

            } else {

                row.style.display = "none";

            }

        });

    });

}); 