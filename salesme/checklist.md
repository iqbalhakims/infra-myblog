# 🚗 Car Sales CRM (MVP) Checklist

## 🧠 Goal

Build a **Salesman CRM** to help sell recon cars faster
(Not a Carsome clone — focus on personal productivity)

---

# 🧱 1. Project Setup

* [ ] Create project folder: `car-sales-crm`
* [ ] Create structure:

  ```
  backend/
  frontend/ (later)
  docker-compose.yml
  ```

---

# ⚙️ 2. Backend Setup (Node.js + Express)

* [ ] Initialize Node.js project

  ```bash
  npm init -y
  ```

* [ ] Install dependencies

  ```bash
  npm install express mysql2 cors dotenv
  ```

* [ ] Create folder structure:

  ```
  src/
    controllers/
    routes/
    models/
    services/
    config/
    app.js
  ```

* [ ] Setup Express server (`app.js`)

* [ ] Enable JSON middleware

* [ ] Setup routes:

  * [ ] `/api/cars`
  * [ ] `/api/leads`
  * [ ] `/api/messages`

---

# 🗄️ 3. Database (MySQL)

* [ ] Create database: `carcrm`

* [ ] Create `cars` table

```sql
CREATE TABLE cars (
  id INT AUTO_INCREMENT PRIMARY KEY,
  model VARCHAR(255),
  price INT,
  mileage INT,
  condition VARCHAR(100),
  status VARCHAR(50) DEFAULT 'available',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

* [ ] Create `leads` table

```sql
CREATE TABLE leads (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255),
  phone VARCHAR(50),
  car_id INT,
  status VARCHAR(50) DEFAULT 'new',
  next_follow_up_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 🚗 4. Cars API

* [ ] Create car

  * `POST /api/cars`

* [ ] Get all cars

  * `GET /api/cars`

* [ ] Update car status

  * `PATCH /api/cars/:id/status`

---

# 👤 5. Leads API

* [ ] Create lead

  * `POST /api/leads`

* [ ] Get all leads

  * `GET /api/leads`

* [ ] Update lead status

  * `PATCH /api/leads/:id`

---

# 💬 6. WhatsApp Message Generator (🔥 Core Feature)

* [ ] Create message service

```js
function generateMessage(car) {
  return `
Hi boss 👋

${car.model}
Mileage: ${car.mileage} km
Price: RM${car.price}

Full loan can arrange ✅
Low deposit ✅

Interested? I can arrange viewing 👍
  `;
}
```

* [ ] API endpoint:

  * `POST /api/messages/generate`

* [ ] Return generated message

---

# 🐳 7. Docker Setup

* [ ] Create `Dockerfile` for backend

* [ ] Create `docker-compose.yml`

```yaml
version: '3'

services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    depends_on:
      - db
    environment:
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=root
      - DB_NAME=carcrm

  db:
    image: mysql:8
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: carcrm
    ports:
      - "3306:3306"
```

* [ ] Run project:

```bash
docker-compose up --build
```

---

# 🧪 8. Testing

* [ ] Use Postman / curl
* [ ] Test all endpoints:

  * [ ] Create car
  * [ ] Create lead
  * [ ] Generate message
  * [ ] Update status

---

# 🎨 9. Frontend (Basic - React)

* [ ] Create simple UI:

  * [ ] Add car form
  * [ ] List cars
  * [ ] Add lead
  * [ ] Generate WhatsApp message button

---

# 🚀 10. Deployment

* [ ] Create DigitalOcean Droplet
* [ ] Install Docker
* [ ] Deploy using docker-compose
* [ ] Open port 3000

---

# 🔥 11. Phase 2 (After MVP)

* [ ] Follow-up reminder system
* [ ] Dashboard:

  * [ ] Total leads
  * [ ] Closed deals
* [ ] Message templates:

  * [ ] Malay version
  * [ ] English version
* [ ] Multi-user support

---

# 🧠 12. Future Scaling (DevOps Mode)

* [ ] Move DB → Managed DB
* [ ] Add Nginx reverse proxy
* [ ] Setup CI/CD (GitHub Actions)
* [ ] Deploy to Kubernetes

---

# 🎯 Final Reminder

* [ ] Focus on **closing deals faster**
* [ ] Use it daily
* [ ] Improve based on real usage
* [ ] Only scale when needed

---

# 🗂️ KIV / Backlog

* [ ] **Image compression on upload** — compress photos to max 1200px wide on upload
  * Current: ~3 MB/photo (raw phone photo)
  * After compression: ~300 KB/photo
  * Impact: 10x more storage capacity (~3,500 cars vs ~350 cars on 25GB droplet)
  * Droplet: $6/mo, 25GB disk, ~18GB usable for uploads
  * Each car = 15-20 photos × 3MB = ~51MB uncompressed, ~5MB compressed
