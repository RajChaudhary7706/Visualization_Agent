import { useState } from "react";

const ProjectInputForm = ({ onAnalyze }) => {
  const [githubUrl, setGithubUrl] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onAnalyze({ github_url: githubUrl });
  };

  return (
    <div className="p-6 bg-gray-900 rounded-xl shadow-lg">
      <h2 className="text-xl font-bold mb-4">Analyze Project</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter GitHub Repo URL"
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
          className="w-full p-2 mb-4 rounded bg-gray-800 text-white"
        />

        <button className="bg-blue-600 px-4 py-2 rounded hover:bg-blue-700">
          Analyze
        </button>
      </form>
    </div>
  );
};

export default ProjectInputForm;
