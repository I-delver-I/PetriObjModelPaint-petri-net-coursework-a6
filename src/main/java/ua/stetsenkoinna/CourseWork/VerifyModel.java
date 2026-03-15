package ua.stetsenkoinna.CourseWork;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.IOException;
import java.util.LinkedList;
import java.util.Locale;
import java.util.Queue;
import ua.stetsenkoinna.PetriObj.PetriP;

public class VerifyModel {

    public static void main(String[] args) throws Exception {
        double simulationTime = 700000.0;
        double logInterval = 100.0;

        final double[] crusherUnload20t = { 5.0, 10.0,  5.0,  5.0,  5.0 };
        final double[] crusherUnload50t = { 4.0,  8.0,  4.0,  4.0,  4.0 };
        final double[] excavatorLoad20t = { 5.0,  5.0,  2.5,  5.0,  5.0 };
        final int[] extraTrucks50t =      {   0,    0,    0,    1,    0 };
        final int[] priority50t =         {   1,    1,    1,    1,    0 };

        int numRunsPerSet = 5;

        System.out.println("Starting Deep Verification (5 Sets x 5 Runs = 25 total runs)...");

        for (int setIdx = 0; setIdx < crusherUnload20t.length; setIdx++) {
            String setDirName = "Set_" + setIdx + "/";
            File setDir = new File(setDirName);
            if (!setDir.exists()) setDir.mkdir();

            System.out.println("Processing Parameter Set " + setIdx + "...");

            for (int run = 1; run <= numRunsPerSet; run++) {
                String runDirName = setDirName + "Run_" + run + "/";
                File runDir = new File(runDirName);
                if (!runDir.exists()) runDir.mkdir();

                ExcavatorCrusherNet systemNet = new ExcavatorCrusherNet(
                        crusherUnload20t[setIdx], crusherUnload50t[setIdx], 
                        excavatorLoad20t[setIdx], extraTrucks50t[setIdx], priority50t[setIdx]
                );

                CourseWorkPetriSim sim = new CourseWorkPetriSim(systemNet.net);

                runAndLog(sim, systemNet, runDirName, simulationTime, logInterval, run);
            }
        }
        System.out.println("All 25 runs completed successfully!");
    }

    private static void runAndLog(CourseWorkPetriSim sim, ExcavatorCrusherNet systemNet, 
        String dirName, double simulationTime, double logInterval, int runIdx) {
        
        @SuppressWarnings("unchecked")
        Queue<Double>[] waitQueues = new Queue[6];
        int[] prevMarks = new int[6];
        for (int i = 0; i < 6; i++) {
            waitQueues[i] = new LinkedList<>();
            prevMarks[i] = 0;
        }

        try (PrintWriter statsWriter = new PrintWriter(new FileWriter(dirName + "simulation_stats.csv"));
             PrintWriter waitWriter = new PrintWriter(new FileWriter(dirName + "wait_times.csv"))) {

            statsWriter.println("Run,Time,Crusher Utilization,Average Crusher Queue," +
                    "Excavator 1 Utilization,Excavator 1 Average Queue," +
                    "Excavator 2 Utilization,Excavator 2 Average Queue," +
                    "Excavator 3 Utilization,Excavator 3 Average Queue");
            waitWriter.println("Run,Time,TruckType,WaitTime");

            double[] nextLogTime = { 0.0 };

            sim.go(simulationTime, (time) -> {
                for (int i = 0; i < 6; i++) {
                    int currentMark = systemNet.waitCrusherPlaces.get(i).getMark();
                    if (currentMark > prevMarks[i]) {
                        for (int j = 0; j < currentMark - prevMarks[i]; j++) waitQueues[i].add(time);
                    } else if (currentMark < prevMarks[i]) {
                        for (int j = 0; j < prevMarks[i] - currentMark; j++) {
                            if (!waitQueues[i].isEmpty()) {
                                double arrivalTime = waitQueues[i].poll();
                                double waitTime = time - arrivalTime;
                                int truckType = (i % 2 == 0) ? 20 : 50;
                                waitWriter.printf(Locale.US, "%d,%.2f,%d,%.4f%n", runIdx, time, truckType, waitTime);
                            }
                        }
                    }
                    prevMarks[i] = currentMark;
                }

                if (time >= nextLogTime[0]) { 
                    double crusherUtil = systemNet.freeCrusher.getMark() == 0 ? 1.0 : 0.0;
                    double crusherQueue = 0.0;
                    for (PetriP p : systemNet.waitCrusherPlaces) {
                        crusherQueue += p.getMark();
                    }

                    double exc1Util = systemNet.freeExcavators.get(0).getMark() == 0 ? 1.0 : 0.0;
                    double exc1Queue = systemNet.waitExcavatorPlaces.get(0).getMark() 
                        + systemNet.waitExcavatorPlaces.get(1).getMark();

                    double exc2Util = systemNet.freeExcavators.get(1).getMark() == 0 ? 1.0 : 0.0;
                    double exc2Queue = systemNet.waitExcavatorPlaces.get(2).getMark() 
                        + systemNet.waitExcavatorPlaces.get(3).getMark();

                    double exc3Util = systemNet.freeExcavators.get(2).getMark() == 0 ? 1.0 : 0.0;
                    double exc3Queue = systemNet.waitExcavatorPlaces.get(4).getMark() 
                        + systemNet.waitExcavatorPlaces.get(5).getMark();

                    statsWriter.printf(Locale.US, "%d,%.2f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f%n",
                            runIdx, time, crusherUtil, crusherQueue, 
                            exc1Util, exc1Queue, exc2Util, exc2Queue, exc3Util, exc3Queue);
                    
                    nextLogTime[0] += logInterval;
                }
            });

        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
        }
    }
}