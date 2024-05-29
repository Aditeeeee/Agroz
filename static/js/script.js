const API_KEY = "49287276118b089ee94e7a10946443cf";
const weatherInfo = document.getElementById("weatherInfo");
const temperatureInput = document.getElementById("temperature");
const humidityInput = document.getElementById("humidity");

function getWeather() {
  const city = document.getElementById("city").value.trim();
  if (!city) {
    alert("Please enter a city name.");
    return;
  }
  fetchWeather(city);
}

function fetchWeather(city) {
  fetch(
    `http://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${API_KEY}`
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.cod === 200) {
        weatherInfo.style.display = "block";
        temperatureInput.value = (data.main.temp - 273.15).toFixed(2);
        humidityInput.value = parseFloat(data.main.humidity);
        document.querySelector('button[type="submit"]').disabled = false;
      } else {
        alert(`Failed to fetch weather data: ${data.message}`);
      }
    })
    .catch((error) => {
      console.error("Error fetching weather data:", error);
      alert("An error occurred while fetching weather data.");
    });
}

document.getElementById("taluka").addEventListener("change", function () {
  var taluka = this.value;
  var revenueVillageSelect = document.getElementById("revenue_village");
  revenueVillageSelect.innerHTML = "";

  var villageOptions;
  switch (taluka) {
    case "Pernem":
      villageOptions = ["Arambol", "Querim", "Pernem", "Chaudi"];
      break;

    case "Bardez":
      villageOptions = ["Calangute", "Candolim", "Baga", "Anjuna", "Aldona", "Socorro"];
      break;
    
      case "Bicholim":
      villageOptions = ["Astagiri", "Surla", "Mayem", "Sanquelim"];
      break;
    
      case "Sattari":
      villageOptions = ["Valpoi", "Curti", "Borim", "Nagoa"];
      break;
    
      case "Tiswadi":
      villageOptions = ["Panaji", "Taleigao", "Ribandar", "Goa Velha"];
      break;
    
      case "Ponda":
      villageOptions = ["Shantadurga", "Mangueshi", "Bandora", "Curti"];
      break;

      case "Mormugao":
      villageOptions = ["Vasco da Gama", "Dabolim", "Sancoale", "Arossim"];
      break;

      case "Salcete":
      villageOptions = ["Margao", "Colva", "Mobor", "Betalbatim", "Navelim"];
      break;

      case "Sanguem":
      villageOptions = ["Sanguem", "Curchorem", "Uguem", "Sanvordem"];
      break;

      case "Quepem":
      villageOptions = ["Quepem", "Netravali", "Cuncolim", "Cavra"];
      break;

      case "Dharbandora":
      villageOptions = ["Dharbandora", "Curti", "Cola", "Pilar"];
      break;

      case "Canacona":
      villageOptions = ["Canacona", "Chaudi", "Agonda", "Poinguinim", "Palolem"];
      break;
    
    default:
      villageOptions = ["Select Taluka first"];
      break;
  }

  villageOptions.forEach(function (option) {
    var villageOption = document.createElement("option");
    villageOption.value = option;
    villageOption.textContent = option;
    revenueVillageSelect.appendChild(villageOption);
  });
});

async function fetchNews() {
  try {
    const response = await fetch('/get_news');
    const newsData = await response.json();
    if (response.ok) {
      displayNews(newsData.articles);
      createSlideshow(); // Call createSlideshow only once after successful fetch
    } else {
      console.error('Failed to fetch news');
    }
  } catch (error) {
    console.error('Error fetching news:', error);
  }
}

function displayNews(articles) {
  const newsSlides = document.querySelector('.news-slides');
  articles.forEach(article => {
    const newsItem = document.createElement('div');
    newsItem.classList.add('news-item');
    newsItem.innerHTML = `
      <a href="${article.url}" target="_blank">
        <h3>${article.title}</h3>
        <p>${article.description}</p>
      </a>
    `;
    newsSlides.appendChild(newsItem);
  });
}

function createSlideshow() {
  const newsSlides = document.querySelector('.news-slides');
  const newsItems = newsSlides.querySelectorAll('.news-item');
  let currentSlide = 0;
  const slideInterval = 7000; // Change this value to adjust transition interval in milliseconds

  function showSlide() {
    newsItems.forEach((item, index) => {
      item.style.display = index === currentSlide ? 'block' : 'none';
    });
  }

  function nextSlide() {
    currentSlide = (currentSlide + 1) % newsItems.length;
    showSlide();
  }

  function prevSlide() {
    currentSlide = (currentSlide - 1 + newsItems.length) % newsItems.length;
    showSlide();
  }

  // Show the initial slide
  showSlide();
  // Set up automatic slide transitions
  const intervalId = setInterval(nextSlide, slideInterval);
}

fetchNews(); // Call fetchNews only once
