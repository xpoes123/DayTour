# DayTour 🗺️

**DayTour** is a web application for planning, organizing, and visualizing **multi-stop day itineraries**.  
It allows users to build a sequence of stops for a day, manage and reorder locations, and view their plan through a clean, simple interface.

---

## ✨ Why DayTour?

- Build a complete day itinerary without spreadsheets or scattered notes  
- Add, reorder, and organize stops in a logical flow  
- Designed as a lightweight personal tool for planning travel days or tours  

---

## 🛠️ Technology Stack

DayTour is built using:

- **Django** — backend, routing, itinerary models  
- **HTML / CSS / JavaScript** — user interface  
- **SQLite** (default) — local development database  
- Django templates & static files for rendering UI  

---

## 🚀 Getting Started (Local Development)

Follow these steps to run DayTour locally:

```bash
# 1. Clone the repository
git clone https://github.com/xpoes123/DayTour.git
cd DayTour

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py migrate

# 5. (Optional) Create an admin user
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver

# Visit in browser:
# http://127.0.0.1:8000/
```

---

## 🎯 Project Status

DayTour is currently a **prototype / personal project**.  
It is functional but not optimized for production or large-scale deployment.  
Use it as-is or as a foundation for future enhancements.

---

## 🔮 Future Improvement Ideas

- Integrate geolocation or mapping APIs  
- Add stop autocomplete, travel time estimation, or mapping  
- Improve UI/UX (drag-and-drop ordering, better layout)  
- Export itineraries (CSV, JSON, sharable links)  
- Expand user authentication and support multiple profiles  
- Migrate to a production database and deployment setup  

---

## 📄 License

No license is currently specified.  
Consider adding the MIT License if open-sourcing or sharing widely.

---

*Project maintained by @xpoes123.*
