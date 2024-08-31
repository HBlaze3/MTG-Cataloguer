const MAIN = ["W", "U", "B", "R", "G", "C"];
const SECONDARY = ["M", "T"];
const TERTIARY = ["A"];
const JSONMAINCATEGORIES = ["name", "type_line", "set_name", "set", "collector_number", "quantity", "quantity_foil", "usd", "usd_foil", "total_usd", "total_usd_foil", "storage_areas", "storage_quantity", "deck_type", "deck_quantity", "deck_type_two", "deck_quantity_two", "deck_type_three", "deck_quantity_three", "deck_type_four", "deck_quantity_four"];
const HTMLMAINCATEGORIES = ["Card Name", "Type", "Set Name", "Set", "Collector #", "Quantity", "Foil Quantity", "Nonfoil", "Foil", "Total Nonfoil Value", "Total Foil Value", "Storage Area(s)", "Storage Quantity", "Deck Type", "Deck Quantity", "Deck Type 2", "Deck Quantity 2", "Deck Type 3", "Deck Quantity 3", "Deck Type 4", "Deck Quantity 4"];
const JSONSECONDARYCATEGORIES = [...JSONMAINCATEGORIES.slice(0, 3), "color_identity", ...JSONMAINCATEGORIES.slice(3)];
const HTMLSECONDARYCATEGORIES = [...HTMLMAINCATEGORIES.slice(0, 3), "Colour(s)", ...HTMLMAINCATEGORIES.slice(3)];
const JSONTERTIARYCATEGORIES = JSONMAINCATEGORIES.slice(0, 6);
const HTMLTERTIARYCATEGORIES = HTMLMAINCATEGORIES.slice(0, 6);
let previousCat = '';

document.getElementById('clearLocalStorage').addEventListener('click', function() {
    const keysToRemove = [...MAIN, ...SECONDARY, ...TERTIARY];
    
    keysToRemove.forEach(key => {
        localStorage.removeItem(key);
    });

    alert("Stored JSON data cleared.");
});

if (localStorage.getItem('darkMode') === 'enabled') {
    document.body.classList.add('dark-mode');
}

document.getElementById('darkModeToggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');

    if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('darkMode', 'enabled');
        } else {
            localStorage.setItem('darkMode', 'disabled');
        }
});

function fillHeader(header) {
  const categories = {
      "TERTIARY": HTMLTERTIARYCATEGORIES,
      "SECONDARY": HTMLSECONDARYCATEGORIES,
      "MAIN": HTMLMAINCATEGORIES
  }[header] || HTMLMAINCATEGORIES;

  const headerHtml = categories.map(item => `<th>${item}</th>`).join('');
  $("#carddata thead").html(headerHtml);
}

function getTbl(jsonset, data) {
  let categories;

  if (TERTIARY.includes(jsonset)) {
      categories = JSONTERTIARYCATEGORIES;
  } else if (SECONDARY.includes(jsonset)) {
      categories = JSONSECONDARYCATEGORIES;
  } else {
      categories = JSONMAINCATEGORIES;
  }

  const rowsHtml = data.map(f => {
      const rowHtml = categories.map(item => {
          const cellContent = item === "set" ? f[item]?.toUpperCase() : f[item] ?? '';
          return `<td>${cellContent}</td>`;
      }).join('');
      return `<tr>${rowHtml}</tr>`;
  }).join('');

  $("#carddata tbody").html(rowsHtml);
}

function grabStoredFiles(jsonset) {
    const storedData = localStorage.getItem(jsonset);

    if (storedData) {
        getTbl(jsonset, JSON.parse(storedData));
    } else {
        $.getJSON(`../JSONs/${jsonset}.json`, function(data) {
            data.forEach(f => {
                delete f["lang"];
                delete f["release_date"];
                if (MAIN.includes(jsonset)) delete f["color_identity"];
            });

            localStorage.setItem(jsonset, JSON.stringify(data));
            getTbl(jsonset, data);
        });
    }
}

$(document).ready(function() {
    $('.tablinks').on('click', function () {
        const grabbedValue = $(this).data("value");
        const [category, index] = grabbedValue;
        const jsonset = {
            "TERTIARY": TERTIARY[index],
            "SECONDARY": SECONDARY[index],
            "MAIN": MAIN[index]
        }[category];

        if (previousCat !== category) {
            fillHeader(category);
            previousCat = category;
        }

        $("#carddata tbody").empty();
        grabStoredFiles(jsonset);
    });

    $('.tablinks').first().trigger('click');
});