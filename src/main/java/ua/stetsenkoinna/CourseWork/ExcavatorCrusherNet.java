package ua.stetsenkoinna.CourseWork;

import ua.stetsenkoinna.PetriObj.*;
import java.util.ArrayList;

public class ExcavatorCrusherNet {
    public final PetriNet net;

    // Store references to places for final statistics
    public final PetriP freeCrusher;
    public final ArrayList<PetriP> freeExcavators = new ArrayList<>();
    public final ArrayList<PetriP> waitExcavatorPlaces = new ArrayList<>();
    public final ArrayList<PetriP> waitCrusherPlaces = new ArrayList<>();

    // --- DEFAULT CONSTRUCTOR ---
    // (Used for a standard run with default parameters)
    public ExcavatorCrusherNet() throws ExceptionInvalidTimeDelay {
        this(5.0, 4.0, 5.0, 0, 1); // Call the parameterized constructor with default values
    }

    // --- PARAMETERIZED CONSTRUCTOR FOR VERIFICATION ---
    public ExcavatorCrusherNet(double crusherUnload20t, double crusherUnload50t, double excavatorLoad20t, int extraTrucks50t, int priority50t) throws ExceptionInvalidTimeDelay {
        ArrayList<PetriP> d_P = new ArrayList<>();
        ArrayList<PetriT> d_T = new ArrayList<>();
        ArrayList<ArcIn> d_In = new ArrayList<>();
        ArrayList<ArcOut> d_Out = new ArrayList<>();

        // Shared crusher (1 token = free resource)
        freeCrusher = new PetriP("Free crusher", 1);
        d_P.add(freeCrusher);

        // Create 3 identical branches for the excavators
        for (int i = 1; i <= 3; i++) {
            // Places
            PetriP pWaitExc20 = new PetriP("Wait excavator " + i + " 20t", 1);
            PetriP pFreeExc = new PetriP("Free excavator " + i, 1);
            
            // VERIFICATION CHANGE: Add extra 50-ton trucks if specified by parameters
            PetriP pWaitExc50 = new PetriP("Wait excavator " + i + " 50t", 1 + extraTrucks50t);

            PetriP pTransToCrush20 = new PetriP("Transit to crusher from excavator " + i + " 20t", 0);
            PetriP pTransToCrush50 = new PetriP("Transit to crusher from excavator " + i + " 50t", 0);

            PetriP pWaitFrom20 = new PetriP("Wait from excavator " + i + " 20t", 0);
            PetriP pWaitFrom50 = new PetriP("Wait from excavator " + i + " 50t", 0);

            PetriP pTransToExc20 = new PetriP("Transit to excavator " + i + " 20t", 0);
            PetriP pTransToExc50 = new PetriP("Transit to excavator " + i + " 50t", 0);

            // Store references for statistics gathering
            freeExcavators.add(pFreeExc);
            waitExcavatorPlaces.add(pWaitExc20);
            waitExcavatorPlaces.add(pWaitExc50);
            waitCrusherPlaces.add(pWaitFrom20);
            waitCrusherPlaces.add(pWaitFrom50);

            d_P.addAll(java.util.Arrays.asList(pWaitExc20, pFreeExc, pWaitExc50, pTransToCrush20, pTransToCrush50, pWaitFrom20, pWaitFrom50, pTransToExc20, pTransToExc50));

            // Transitions
            // VERIFICATION CHANGE: Loading time for 20t truck is now a dynamic variable
            PetriT tLoad20 = new PetriT("Load from excavator " + i + " 20t", excavatorLoad20t);
            tLoad20.setDistribution("exp", tLoad20.getTimeServ());

            PetriT tLoad50 = new PetriT("Load from excavator " + i + " 50t", 10.0);
            tLoad50.setDistribution("exp", tLoad50.getTimeServ());

            // Moving to crusher (Constant time delays)
            PetriT tMoveCrush20 = new PetriT("Move to crusher from excavator " + i + " 20t", 2.5);
            PetriT tMoveCrush50 = new PetriT("Move to crusher from excavator " + i + " 50t", 3.0);

            // Unloading at the crusher
            // VERIFICATION CHANGE: Unloading time for 20t truck is now a dynamic variable
            PetriT tUnload20 = new PetriT("Unload from excavator " + i + " 20t", crusherUnload20t);
            tUnload20.setDistribution("exp", tUnload20.getTimeServ());

            // Priority for 50t trucks at the crusher
            // VERIFICATION CHANGE: Unloading time and priority for 50t truck are now dynamic variables
            PetriT tUnload50 = new PetriT("Unload from excavator " + i + " 50t", crusherUnload50t, priority50t);
            tUnload50.setDistribution("exp", tUnload50.getTimeServ());

            // Return to excavator (Constant time delays)
            PetriT tMoveExc20 = new PetriT("Move to excavator " + i + " 20t", 1.5);
            PetriT tMoveExc50 = new PetriT("Move to excavator " + i + " 50t", 2.0);

            d_T.addAll(java.util.Arrays.asList(tLoad20, tLoad50, tMoveCrush20, tMoveCrush50, tUnload20, tUnload50, tMoveExc20, tMoveExc50));

            // --- Arcs (20-ton truck loop) ---
            d_In.add(new ArcIn(pWaitExc20, tLoad20, 1));
            d_In.add(new ArcIn(pFreeExc, tLoad20, 1)); // Seize the excavator
            d_Out.add(new ArcOut(tLoad20, pTransToCrush20, 1)); // Truck leaves the excavator
            d_Out.add(new ArcOut(tLoad20, pFreeExc, 1)); // Release the excavator immediately

            d_In.add(new ArcIn(pTransToCrush20, tMoveCrush20, 1));
            d_Out.add(new ArcOut(tMoveCrush20, pWaitFrom20, 1)); // Truck arrives at the crusher queue

            d_In.add(new ArcIn(pWaitFrom20, tUnload20, 1));
            d_In.add(new ArcIn(freeCrusher, tUnload20, 1)); // Seize the crusher
            d_Out.add(new ArcOut(tUnload20, pTransToExc20, 1)); // Truck leaves the crusher
            d_Out.add(new ArcOut(tUnload20, freeCrusher, 1)); // Release the crusher

            d_In.add(new ArcIn(pTransToExc20, tMoveExc20, 1));
            d_Out.add(new ArcOut(tMoveExc20, pWaitExc20, 1)); // Truck arrives back at the excavator queue

            // --- Arcs (50-ton truck loop) ---
            d_In.add(new ArcIn(pWaitExc50, tLoad50, 1));
            d_In.add(new ArcIn(pFreeExc, tLoad50, 1)); // Seize the excavator
            d_Out.add(new ArcOut(tLoad50, pTransToCrush50, 1)); // Truck leaves the excavator
            d_Out.add(new ArcOut(tLoad50, pFreeExc, 1)); // Release the excavator immediately

            d_In.add(new ArcIn(pTransToCrush50, tMoveCrush50, 1));
            d_Out.add(new ArcOut(tMoveCrush50, pWaitFrom50, 1)); // Truck arrives at the crusher queue

            d_In.add(new ArcIn(pWaitFrom50, tUnload50, 1));
            d_In.add(new ArcIn(freeCrusher, tUnload50, 1)); // Seize the crusher
            d_Out.add(new ArcOut(tUnload50, pTransToExc50, 1)); // Truck leaves the crusher
            d_Out.add(new ArcOut(tUnload50, freeCrusher, 1)); // Release the crusher

            d_In.add(new ArcIn(pTransToExc50, tMoveExc50, 1));
            d_Out.add(new ArcOut(tMoveExc50, pWaitExc50, 1)); // Truck arrives back at the excavator queue
        }

        net = new PetriNet("ExcavatorsAndCrusher", d_P, d_T, d_In, d_Out);
        PetriP.initNext();
        PetriT.initNext();
        ArcIn.initNext();
        ArcOut.initNext();
    }
}