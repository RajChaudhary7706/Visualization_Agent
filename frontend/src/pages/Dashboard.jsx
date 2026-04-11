import ProjectInputForm from "../components/form/ProjectInputForm";
import { useAnalyze } from "../hooks/useAnalyze";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const { runAnalysis } = useAnalyze();
  const navigate = useNavigate();

  const handleAnalyze = async (data) => {
    await runAnalysis(data);
    navigate("/results", { state: data });
  };

  return (
    <div className="flex justify-center items-center h-screen bg-black text-white">
      <ProjectInputForm onAnalyze={handleAnalyze} />
    </div>
  );
};

export default Dashboard;
