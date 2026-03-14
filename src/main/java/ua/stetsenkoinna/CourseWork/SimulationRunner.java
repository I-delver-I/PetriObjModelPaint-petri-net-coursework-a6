package ua.stetsenkoinna.CourseWork;

import ua.stetsenkoinna.PetriObj.PetriP;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.IOException;
import java.util.LinkedList;
import java.util.Locale;
import java.util.Queue;

public class SimulationRunner {

    public static void main(String[] args) throws Exception {
        double simulationTime = 700000.0;
        double logInterval = 100.0; // Для графіків перехідного періоду

        ExcavatorCrusherNet systemNet = new ExcavatorCrusherNet();
        CourseWorkPetriSim sim = new CourseWorkPetriSim(systemNet.net);

        System.out.println("Starting simulation for " + simulationTime + " minutes...");
        System.out.println("Generating data for Transient Period AND Histograms...");

        // Масиви для відстеження індивідуального часу очікування кожної вантажівки
        @SuppressWarnings("unchecked")
        Queue<Double>[] waitQueues = new Queue[6];
        int[] prevMarks = new int[6];
        for (int i = 0; i < 6; i++) {
            waitQueues[i] = new LinkedList<>();
            prevMarks[i] = 0;
        }

        try (PrintWriter statsWriter = new PrintWriter(new FileWriter("simulation_stats.csv"));
             PrintWriter waitWriter = new PrintWriter(new FileWriter("wait_times.csv"))) {

            // Заголовки файлів
            statsWriter.println("Time,Crusher Utilization,Average Crusher Queue,Excavator 1 Utilization,Excavator 1 Average Queue,Excavator 2 Utilization,Excavator 2 Average Queue,Excavator 3 Utilization,Excavator 3 Average Queue");
            waitWriter.println("Time,TruckType,WaitTime");

            double[] nextLogTime = { logInterval };

            sim.go(simulationTime, (time) -> {

                // --- 1. ЛОГІКА ДЛЯ ГІСТОГРАМ (Індивідуальний час очікування) ---
                for (int i = 0; i < 6; i++) {
                    int currentMark = systemNet.waitCrusherPlaces.get(i).getMark();

                    // Якщо маркерів стало більше -> вантажівка прибула в чергу
                    if (currentMark > prevMarks[i]) {
                        for (int j = 0; j < currentMark - prevMarks[i]; j++) {
                            waitQueues[i].add(time);
                        }
                    }
                    // Якщо маркерів стало менше -> вантажівка вийшла з черги (почала розвантаження)
                    else if (currentMark < prevMarks[i]) {
                        for (int j = 0; j < prevMarks[i] - currentMark; j++) {
                            if (!waitQueues[i].isEmpty()) {
                                double arrivalTime = waitQueues[i].poll();
                                double waitTime = time - arrivalTime;
                                int truckType = (i % 2 == 0) ? 20 : 50; // Парні індекси - 20т, непарні - 50т

                                // Записуємо тільки ті вантажівки, які дійсно чекали
                                waitWriter.printf(Locale.US, "%.2f,%d,%.4f%n", time, truckType, waitTime);
                            }
                        }
                    }
                    prevMarks[i] = currentMark;
                }

                // --- 2. ЛОГІКА ДЛЯ ПЕРЕХІДНОГО ПЕРІОДУ ---
                if (time >= nextLogTime[0]) {
                    double crusherUtil = 1.0 - systemNet.freeCrusher.getMean();
                    double crusherQueue = 0.0;
                    for (PetriP p : systemNet.waitCrusherPlaces) crusherQueue += p.getMean();

                    double exc1Util = 1.0 - systemNet.freeExcavators.get(0).getMean();
                    double exc1Queue = systemNet.waitExcavatorPlaces.get(0).getMean() + systemNet.waitExcavatorPlaces.get(1).getMean();

                    double exc2Util = 1.0 - systemNet.freeExcavators.get(1).getMean();
                    double exc2Queue = systemNet.waitExcavatorPlaces.get(2).getMean() + systemNet.waitExcavatorPlaces.get(3).getMean();

                    double exc3Util = 1.0 - systemNet.freeExcavators.get(2).getMean();
                    double exc3Queue = systemNet.waitExcavatorPlaces.get(4).getMean() + systemNet.waitExcavatorPlaces.get(5).getMean();

                    statsWriter.printf(Locale.US, "%.2f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f%n",
                            time, crusherUtil, crusherQueue, exc1Util, exc1Queue, exc2Util, exc2Queue, exc3Util, exc3Queue);
                    nextLogTime[0] += logInterval;
                }
            });

            System.out.println("Simulation complete! Data saved to 'simulation_stats.csv' and 'wait_times.csv'.");

        } catch (IOException e) {
            System.err.println("Error writing to CSV: " + e.getMessage());
        }
    }
}