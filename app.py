import pickle
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
with open("skill_trend_model.pkl", "rb") as f:
    model = pickle.load(f)

predefined_skills = model["skills"]
skill_frequencies = model["skill_frequencies"]
classification_map = model["classification"]

max_freq = max(skill_frequencies.values()) if skill_frequencies else 1
def clean_text(text: str):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text

def extract_skills(text: str):
    cleaned = clean_text(text)
    detected = []
    for skill in predefined_skills:
        if skill in cleaned:
            detected.append(skill)
    return detected

def classify_skill(skill: str):
    freq = skill_frequencies.get(skill, 0)
    category = classification_map.get(skill, "new/emerging")
    trend_score = round(freq / max_freq, 2)
    return category, trend_score


app = FastAPI(title="Skill Trend Detector API")

# Allow CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobDescription(BaseModel):
    job_description: str

@app.post("/skill-trend")
def skill_trend(payload: JobDescription):
    detected = extract_skills(payload.job_description)
    response = []
    for skill in detected:
        category, trend_score = classify_skill(skill)
        response.append({
            "skill": skill,
            "category": category,
            "trend_score": trend_score
        })
    return {"detected_skills": response}


@app.get("/", response_class=HTMLResponse)
async def frontend(request: Request):
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Skill Trend Detector</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
    h1 { color: #333; }
    textarea { width: 100%; height: 120px; margin-bottom: 15px; padding: 10px; font-size: 16px; }
    button { padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
    button:hover { background-color: #45a049; }
    table { width: 100%; margin-top: 20px; border-collapse: collapse; }
    table, th, td { border: 1px solid #ddd; }
    th, td { padding: 10px; text-align: center; }
    th { background-color: #4CAF50; color: white; }
    tr:nth-child(even) { background-color: #f9f9f9; }
  </style>
</head>
<body>

  <h1>Skill Trend Detector</h1>
  <p>Enter a job description below to detect technical skills and their trend classification:</p>

  <textarea id="jobDescription" placeholder="Paste job description here..."></textarea>
  <br>
  <button onclick="analyzeSkills()">Analyze Skills</button>

  <table id="resultsTable" style="display:none;">
    <thead>
      <tr>
        <th>Skill</th>
        <th>Category</th>
        <th>Trend Score</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <script>
    async function analyzeSkills() {
      const description = document.getElementById("jobDescription").value;
      if (!description.trim()) {
        alert("Please enter a job description!");
        return;
      }

      const response = await fetch("/skill-trend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_description: description })
      });

      const data = await response.json();
      const table = document.getElementById("resultsTable");
      const tbody = table.querySelector("tbody");
      tbody.innerHTML = "";

      if (data.detected_skills.length === 0) {
        tbody.innerHTML = "<tr><td colspan='3'>No skills detected</td></tr>";
      } else {
        data.detected_skills.forEach(skill => {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${skill.skill}</td>
            <td>${skill.category}</td>
            <td>${skill.trend_score}</td>
          `;
          tbody.appendChild(row);
        });
      }

      table.style.display = "table";
    }
  </script>

</body>
</html>
    """
