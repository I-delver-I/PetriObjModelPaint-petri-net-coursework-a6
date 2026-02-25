package ua.stetsenkoinna.CourseWork;

import ua.stetsenkoinna.PetriObj.PetriP;

public class SimulationRunner {

    public static void main(String[] args) throws Exception {
        double simulationTime = 700000.0;

        // Set this to TRUE if you want the massive step-by-step event log
        boolean printDetailedLogs = false;

        ExcavatorCrusherNet systemNet = new ExcavatorCrusherNet();
        CourseWorkPetriSim sim = new CourseWorkPetriSim(systemNet.net);

        System.out.println("Starting simulation...");

        sim.go(simulationTime, (time) -> {
            if (printDetailedLogs) {
                System.out.println("\nTime progress: time = " + time);
                sim.printMark();
            }
        });

        // Extract and print the correct statistics
        System.out.println("\n====== SIMULATION RESULTS ======");
        System.out.println("Simulation time: " + simulationTime + " minutes\n");

        // 1. Crusher utilization rate (1.0 - mean of the free state)
        double crusherLoad = 1.0 - systemNet.freeCrusher.getMean();
        System.out.printf("Crusher utilization rate: %.4f%n", crusherLoad);

        // 2. Average number of trucks in the crusher queue
        double averageQueueCrusher = 0.0;
        for (PetriP p : systemNet.waitCrusherPlaces) {
            averageQueueCrusher += p.getMean();
        }
        System.out.printf("Average number of trucks in the crusher queue: %.4f%n\n", averageQueueCrusher);

        // 3. Statistics for each excavator
        for (int i = 0; i < 3; i++) {
            double excLoad = 1.0 - systemNet.freeExcavators.get(i).getMean();

            double queue20 = systemNet.waitExcavatorPlaces.get(i * 2).getMean();
            double queue50 = systemNet.waitExcavatorPlaces.get(i * 2 + 1).getMean();
            double totalQueueExc = queue20 + queue50;

            System.out.printf("--- Excavator %d ---%n", (i + 1));
            System.out.printf("Utilization rate: %.4f%n", excLoad);
            System.out.printf("Average number of trucks in queue: %.4f%n", totalQueueExc);
        }
    }
}