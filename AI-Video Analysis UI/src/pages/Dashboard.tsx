import { useState, useEffect } from "react";
import { MetricCard } from "@/components/MetricCard";
import { VideoUploader } from "@/components/VideoUploader";
import { AnalyticsChart } from "@/components/AnalyticsChart";
import { SessionControls } from "@/components/SessionControls";
import { Users, CreditCard, Eye, TrendingUp } from "lucide-react";

interface DashboardData {
  totalPeople: number;
  totalPayments: number;
  uniqueCustomers: number;
  reidentificationRate: number;
  paymentBreakdown: Array<{ type: string; count: number; percentage: number }>;
  hourlyActivity: Array<{ hour: string; people: number; payments: number }>;
}

const Dashboard = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId] = useState(() => `sess_${Date.now()}`);
  const [isSessionActive, setIsSessionActive] = useState(true);
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    totalPeople: 0,
    totalPayments: 0,
    uniqueCustomers: 0,
    reidentificationRate: 0,
    paymentBreakdown: [
      { type: "Card", count: 0, percentage: 0 },
      { type: "Cash", count: 0, percentage: 0 }
    ],
    hourlyActivity: []
  });

  // Generate sample hourly data for demo
  useEffect(() => {
    const hours = Array.from({ length: 12 }, (_, i) => {
      const hour = (9 + i).toString().padStart(2, '0') + ':00';
      return {
        hour,
        people: Math.floor(Math.random() * 15) + 5,
        payments: Math.floor(Math.random() * 10) + 2
      };
    });
    
    setDashboardData(prev => ({
      ...prev,
      hourlyActivity: hours
    }));
  }, []);

  const handleVideoUpload = (file: File) => {
    setIsProcessing(true);
    
    // Simulate processing
    setTimeout(() => {
      // Update with sample data after "processing"
      setDashboardData({
        totalPeople: 127,
        totalPayments: 89,
        uniqueCustomers: 105,
        reidentificationRate: 92.5,
        paymentBreakdown: [
          { type: "Card", count: 65, percentage: 73 },
          { type: "Cash", count: 24, percentage: 27 }
        ],
        hourlyActivity: dashboardData.hourlyActivity
      });
      setIsProcessing(false);
    }, 3000);
  };

  const handleNewSession = () => {
    setDashboardData({
      totalPeople: 0,
      totalPayments: 0,
      uniqueCustomers: 0,
      reidentificationRate: 0,
      paymentBreakdown: [
        { type: "Card", count: 0, percentage: 0 },
        { type: "Cash", count: 0, percentage: 0 }
      ],
      hourlyActivity: dashboardData.hourlyActivity
    });
  };

  const handleClearData = () => {
    handleNewSession();
  };

  const handleToggleSession = () => {
    setIsSessionActive(!isSessionActive);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Retail Analytics Dashboard</h1>
          <p className="text-muted-foreground text-lg">
            AI-powered person detection, counting, and payment classification system
          </p>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total People Detected"
            value={dashboardData.totalPeople}
            icon={Users}
            subtitle="Across all sessions"
          />
          <MetricCard
            title="Total Payments"
            value={dashboardData.totalPayments}
            icon={CreditCard}
            variant="success"
            subtitle="Card and cash combined"
          />
          <MetricCard
            title="Unique Customers"
            value={dashboardData.uniqueCustomers}
            icon={Eye}
            subtitle="Through face re-identification"
          />
          <MetricCard
            title="Re-ID Accuracy"
            value={`${dashboardData.reidentificationRate}%`}
            icon={TrendingUp}
            variant="warning"
            subtitle="Customer recognition rate"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Upload and Controls */}
          <div className="space-y-6">
            <VideoUploader
              onVideoUpload={handleVideoUpload}
              isProcessing={isProcessing}
            />
            <SessionControls
              sessionId={sessionId}
              isActive={isSessionActive}
              onNewSession={handleNewSession}
              onClearData={handleClearData}
              onToggleSession={handleToggleSession}
            />
          </div>

          {/* Right Column - Analytics */}
          <div className="lg:col-span-2">
            <AnalyticsChart
              paymentData={dashboardData.paymentBreakdown}
              hourlyData={dashboardData.hourlyActivity}
            />
          </div>
        </div>

        {/* Processing Status */}
        {isProcessing && (
          <div className="fixed bottom-4 right-4 bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg animate-pulse">
            Processing video... Please wait.
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;