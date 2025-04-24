// Fetch data from the backend API
// fetch("http://localhost:8000/api/cache")
//   .then((response) => {
//     if (!response.ok) {
//       throw new Error(`HTTP error! Status: ${response.status}`);
//     }
//     return response.json();
//   })
// .then((data) => {
//   console.log("Data fetched:", data); // Check if data is loaded in console
//   populateTable(data); // Fill the table
// })
// .catch((error) => {
//   console.error("Error fetching data:", error);
//   // Display an error message to the user
//   const tableBody = document.getElementById("token-table");
//   tableBody.innerHTML = `<tr><td colspan="3" class="text-center text-red-500">Failed to load data. Please try again later.</td></tr>`;
// });


function fetchDataAndUpdateTable() {
  try {
    fetch("http://localhost:8000/api/cache")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("Data fetched:", data); // log the fetched data
        populateTable(data); // update the table
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
        const tableBody = document.getElementById("token-table");
        tableBody.innerHTML = `<tr><td colspan="3" class="text-center text-red-500">Failed to load data. Please try again later.</td></tr>`;
      });
  } catch (error) {
    console.error("Unexpected error: ", error);
  }
}

setInterval(fetchDataAndUpdateTable, 3000);

// Function to populate table with JSON data
function populateTable(data) {
  const tableBody = document.getElementById("token-table");

  // Clear any existing rows
  tableBody.innerHTML = "";

  // Loop through JSON data and add rows to table
  data.forEach((item, index) => {
    let row = `<tr class="${index % 2 === 0 ? "bg-white" : "bg-gray-100"}">
                 <td class="px-8 py-8 text-center ">${index + 1}</td>
                 <td class="px-10 py-8 text-center ">${item.website_name}</td>
                 <td class="px-4 py-8 text-center  ">${item.flagged_count}</td>
               </tr>`;
    tableBody.innerHTML += row;
  });
}
