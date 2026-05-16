import { useEffect, useState } from "react";
import axios from "axios";

type Project = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
};

const API_URL = "http://localhost:8000";

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const fetchProjects = async () => {
    const res = await axios.get(`${API_URL}/projects`);
    setProjects(res.data);
  };

  const createProject = async () => {
    if (!name.trim()) return;

    await axios.post(`${API_URL}/projects`, {
      name,
      description,
    });

    setName("");
    setDescription("");
    await fetchProjects();
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>AI Project Manager</h1>
      <p>MCP-powered project planning assistant</p>

      <div style={{ marginTop: "30px" }}>
        <h2>Create Project</h2>

        <input
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ display: "block", width: "300px", padding: "10px" }}
        />

        <textarea
          placeholder="Project description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{
            display: "block",
            width: "300px",
            padding: "10px",
            marginTop: "10px",
          }}
        />

        <button onClick={createProject} style={{ marginTop: "10px" }}>
          Create Project
        </button>
      </div>

      <div style={{ marginTop: "30px" }}>
        <h2>Projects</h2>

        {projects.map((project) => (
          <div
            key={project.id}
            style={{
              border: "1px solid #ccc",
              padding: "15px",
              marginTop: "10px",
              borderRadius: "8px",
            }}
          >
            <h3>{project.name}</h3>
            <p>{project.description}</p>
            <small>Status: {project.status}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;