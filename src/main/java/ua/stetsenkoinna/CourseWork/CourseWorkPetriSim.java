package ua.stetsenkoinna.CourseWork;

import ua.stetsenkoinna.PetriObj.*;
import java.util.*;
import java.util.function.Consumer;

public class CourseWorkPetriSim {
    private final StateTime timeState = new StateTime();
    private double timeMin;
    private final PetriP[] listP;
    private final PetriT[] listT;
    private PetriT eventMin;

    // --- THE SHADOW TRACKER FOR FIFO ---
    // Maps Place Index -> Queue of Token Arrival Times
    private final Map<Integer, Deque<Double>> fifoTracker = new HashMap<>();

    public CourseWorkPetriSim(PetriNet net) {
        timeMin = Double.MAX_VALUE;
        listP = net.getListP();
        listT = net.getListT();
        eventMin = this.getEventMin();

        // Initialize the shadow tracker for every place
        for (int i = 0; i < listP.length; i++) {
            fifoTracker.put(i, new ArrayDeque<>());
            // Initial tokens in the network are assumed to have arrived at t=0.0
            for (int j = 0; j < listP[i].getMark(); j++) {
                fifoTracker.get(i).addLast(0.0);
            }
        }
    }

    public void go(final double timeModelling, final Consumer<Double> trackStats) {
        setSimulationTime(timeModelling);
        setTimeCurr(0);
        input();
        while (getCurrentTime() < getSimulationTime()) {
            trackStats.accept(getCurrentTime());

            // --- CALCULATE STATISTICS ---
            double nextTime = getTimeMin();
            if (nextTime > getSimulationTime()) {
                nextTime = getSimulationTime(); // Prevent overshooting the max time
            }

            double dt = nextTime - getCurrentTime();

            if (dt > 0) { // Оновлюємо статистику тільки якщо час дійсно просунувся
                for (PetriP p : listP) {
                    p.changeMean(dt);
                }
                for (PetriT t : listT) {
                    t.changeMean(dt);
                }
            }
            // ---------------------------------

            setTimeCurr(getTimeMin());
            if (getCurrentTime() <= getSimulationTime()) {
                output();
                input();
            }
        }
    }

    public void printMark() {
        System.out.print("Mark in Net: ");
        for (PetriP position : listP) {
            System.out.print(position.getMark() + "  ");
        }
        System.out.println();
    }

    private void input() {
        ArrayList<PetriT> activeT = this.findActiveT();
        if (activeT.isEmpty() && isBufferEmpty()) {
            timeMin = Double.MAX_VALUE;
        } else {
            while (!activeT.isEmpty()) {
                // Snapshot before token removal
                int[] marksBefore = getMarksSnapshot();

                this.doConflict(activeT).actIn(listP, this.getCurrentTime()); // Note: actIn doesn't need currentTime in standard library, but if your lib requires it, leave it

                // Snapshot after token removal
                int[] marksAfter = getMarksSnapshot();
                updateFifoRemovals(marksBefore, marksAfter);

                activeT = this.findActiveT();
            }
            this.eventMin();
        }
    }

    private void output() {
        if (this.getCurrentTime() <= this.getSimulationTime()) {
            // Snapshot before tokens are added
            int[] marksBefore = getMarksSnapshot();

            // Perform standard outputs
            eventMin.actOut(listP, this.getCurrentTime());
            if (eventMin.getBuffer() > 0) {
                boolean u = true;
                while (u) {
                    eventMin.minEvent();
                    if (eventMin.getMinTime() == this.getCurrentTime()) {
                        eventMin.actOut(listP, this.getCurrentTime());
                    } else {
                        u = false;
                    }
                }
            }
            for (PetriT transition : listT) {
                if (transition.getBuffer() > 0 && transition.getMinTime() == this.getCurrentTime()) {
                    transition.actOut(listP, this.getCurrentTime());
                    if (transition.getBuffer() > 0) {
                        boolean u = true;
                        while (u) {
                            transition.minEvent();
                            if (transition.getMinTime() == this.getCurrentTime()) {
                                transition.actOut(listP, this.getCurrentTime());
                            } else {
                                u = false;
                            }
                        }
                    }
                }
            }

            // Snapshot after tokens are added, and record the arrival time
            int[] marksAfter = getMarksSnapshot();
            updateFifoAdditions(marksBefore, marksAfter, this.getCurrentTime());
        }
    }

    // --- FIFO TRACKING LOGIC ---

    private int[] getMarksSnapshot() {
        int[] marks = new int[listP.length];
        for (int i = 0; i < listP.length; i++) {
            marks[i] = listP[i].getMark();
        }
        return marks;
    }

    private void updateFifoAdditions(int[] before, int[] after, double currentTime) {
        for (int i = 0; i < before.length; i++) {
            int diff = after[i] - before[i];
            for (int k = 0; k < diff; k++) {
                fifoTracker.get(i).addLast(currentTime);
            }
        }
    }

    private void updateFifoRemovals(int[] before, int[] after) {
        for (int i = 0; i < before.length; i++) {
            int diff = before[i] - after[i];
            for (int k = 0; k < diff; k++) {
                fifoTracker.get(i).pollFirst();
            }
        }
    }

    // --- CONFLICT RESOLUTION ---

    private PetriT doConflict(ArrayList<PetriT> transitions) {
        PetriT aT = transitions.get(0);
        if (transitions.size() > 1) {
            aT = transitions.get(0);
            int i = 0;
            while (i < transitions.size() && transitions.get(i).getPriority() == aT.getPriority()) {
                i++;
            }
            if (i != 1) {
                int sharedPlace = findSharedInputPlace(transitions, i);

                if (sharedPlace >= 0) {
                    // FIFO Rule applied externally!
                    double earliestTime = Double.MAX_VALUE;
                    PetriT fifoWinner = null;
                    for (int j = 0; j < i; j++) {
                        PetriT candidate = transitions.get(j);
                        double candidateEarliest = getEarliestNonSharedInputArrival(candidate, sharedPlace);
                        if (candidateEarliest < earliestTime) {
                            earliestTime = candidateEarliest;
                            fifoWinner = candidate;
                        }
                    }
                    if (fifoWinner != null) {
                        aT = fifoWinner;
                    }
                } else {
                    // Standard probability rule
                    double r = Math.random();
                    int j = 0;
                    double sum = 0;
                    double prob;
                    while (j < transitions.size() && transitions.get(j).getPriority() == aT.getPriority()) {
                        if (transitions.get(j).getProbability() == 1.0) {
                            prob = 1.0 / i;
                        } else {
                            prob = transitions.get(j).getProbability();
                        }
                        sum += prob;
                        if (r < sum) {
                            aT = transitions.get(j);
                            break;
                        } else {
                            j++;
                        }
                    }
                }
            }
        }
        return aT;
    }

    private int findSharedInputPlace(ArrayList<PetriT> transitions, int count) {
        if (count < 2) return -1;
        ArrayList<Integer> firstInP = transitions.get(0).getInP();
        for (int placeIdx : firstInP) {
            boolean sharedByAll = true;
            for (int j = 1; j < count; j++) {
                if (!transitions.get(j).getInP().contains(placeIdx)) {
                    sharedByAll = false;
                    break;
                }
            }
            if (sharedByAll) return placeIdx;
        }
        return -1;
    }

    private double getEarliestNonSharedInputArrival(PetriT transition, int sharedPlace) {
        double earliest = Double.MAX_VALUE;
        for (int idx : transition.getInP()) {
            if (idx != sharedPlace) {
                Deque<Double> q = fifoTracker.get(idx);
                double t = (q == null || q.isEmpty()) ? Double.MAX_VALUE : q.peekFirst();
                if (t < earliest) earliest = t;
            }
        }
        // Fallback if the shared place is the only input
        if (earliest == Double.MAX_VALUE) {
            Deque<Double> q = fifoTracker.get(sharedPlace);
            earliest = (q == null || q.isEmpty()) ? Double.MAX_VALUE : q.peekFirst();
        }
        return earliest;
    }

    // --- UTILITY METHODS ---

    private void eventMin() {
        PetriT event = null;
        double min = Double.MAX_VALUE;
        for (PetriT transition : listT) {
            if (transition.getMinTime() < min) {
                event = transition;
                min = transition.getMinTime();
            }
        }
        timeMin = min;
        eventMin = event;
    }

    private double getTimeMin() {
        return timeMin;
    }

    private ArrayList<PetriT> findActiveT() {
        ArrayList<PetriT> aT = new ArrayList<>();
        for (PetriT transition : listT) {
            if ((transition.condition(listP)) && (transition.getProbability() != 0)) {
                aT.add(transition);
            }
        }
        if (aT.size() > 1) {
            aT.sort((o1, o2) -> Integer.compare(o2.getPriority(), o1.getPriority()));
        }
        return aT;
    }

    private double getCurrentTime() {
        return timeState.getCurrentTime();
    }

    private void setTimeCurr(double aTimeCurr) {
        timeState.setCurrentTime(aTimeCurr);
    }

    private double getSimulationTime() {
        return timeState.getSimulationTime();
    }

    private void setSimulationTime(double aTimeMod) {
        timeState.setSimulationTime(aTimeMod);
    }

    private boolean isBufferEmpty() {
        boolean c = true;
        for (PetriT e : listT) {
            if (e.getBuffer() > 0) {
                c = false;
                break;
            }
        }
        return c;
    }

    private PetriT getEventMin() {
        this.eventMin();
        return eventMin;
    }
}