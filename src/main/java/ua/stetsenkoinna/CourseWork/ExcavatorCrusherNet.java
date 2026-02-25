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

    public ExcavatorCrusherNet() throws ExceptionInvalidTimeDelay {
        ArrayList<PetriP> d_P = new ArrayList<>();
        ArrayList<PetriT> d_T = new ArrayList<>();
        ArrayList<ArcIn> d_In = new ArrayList<>();
        ArrayList<ArcOut> d_Out = new ArrayList<>();

        // Shared crusher (1 token = free)
        freeCrusher = new PetriP("Free crusher", 1);
        d_P.add(freeCrusher);

        // Create 3 identical branches for excavators
        for (int i = 1; i <= 3; i++) {
            // Places
            PetriP pWaitExc20 = new PetriP("Wait excavator " + i + " 20t", 1);
            PetriP pFreeExc = new PetriP("Free excavator " + i, 1);
            PetriP pWaitExc50 = new PetriP("Wait excavator " + i + " 50t", 1);

            PetriP pTransToCrush20 = new PetriP("Transit to crusher from excavator " + i + " 20t", 0);
            PetriP pTransToCrush50 = new PetriP("Transit to crusher from excavator " + i + " 50t", 0);

            PetriP pWaitFrom20 = new PetriP("Wait from excavator " + i + " 20t", 0);
            PetriP pWaitFrom50 = new PetriP("Wait from excavator " + i + " 50t", 0);

            PetriP pTransToExc20 = new PetriP("Transit to excavator " + i + " 20t", 0);
            PetriP pTransToExc50 = new PetriP("Transit to excavator " + i + " 50t", 0);

            // Store for statistics
            freeExcavators.add(pFreeExc);
            waitExcavatorPlaces.add(pWaitExc20);
            waitExcavatorPlaces.add(pWaitExc50);
            waitCrusherPlaces.add(pWaitFrom20);
            waitCrusherPlaces.add(pWaitFrom50);

            d_P.addAll(java.util.Arrays.asList(pWaitExc20, pFreeExc, pWaitExc50, pTransToCrush20, pTransToCrush50, pWaitFrom20, pWaitFrom50, pTransToExc20, pTransToExc50));

            // Transitions (according to Table 2.2)
            PetriT tLoad20 = new PetriT("Load from excavator " + i + " 20t", 5.0);
            tLoad20.setDistribution("exp", tLoad20.getTimeServ());

            PetriT tLoad50 = new PetriT("Load from excavator " + i + " 50t", 10.0);
            tLoad50.setDistribution("exp", tLoad50.getTimeServ());

            // Moving to crusher (Constants)
            PetriT tMoveCrush20 = new PetriT("Move to crusher from excavator " + i + " 20t", 2.5); // Corrected to 2.5
            PetriT tMoveCrush50 = new PetriT("Move to crusher from excavator " + i + " 50t", 3.0);

            // Unloading
            PetriT tUnload20 = new PetriT("Unload from excavator " + i + " 20t", 5.0);
            tUnload20.setDistribution("exp", tUnload20.getTimeServ());

            // Priority for 50t trucks at the crusher (Priority = 1)
            PetriT tUnload50 = new PetriT("Unload from excavator " + i + " 50t", 4.0, 1);
            tUnload50.setDistribution("exp", tUnload50.getTimeServ());

            // Return to excavator (Constants)
            PetriT tMoveExc20 = new PetriT("Move to excavator " + i + " 20t", 1.5);
            PetriT tMoveExc50 = new PetriT("Move to excavator " + i + " 50t", 2.0);

            d_T.addAll(java.util.Arrays.asList(tLoad20, tLoad50, tMoveCrush20, tMoveCrush50, tUnload20, tUnload50, tMoveExc20, tMoveExc50));

            // --- Arcs (20t) ---
            d_In.add(new ArcIn(pWaitExc20, tLoad20, 1));
            d_In.add(new ArcIn(pFreeExc, tLoad20, 1)); // Seize excavator
            d_Out.add(new ArcOut(tLoad20, pTransToCrush20, 1)); // Truck leaves
            d_Out.add(new ArcOut(tLoad20, pFreeExc, 1)); // RELEASE EXCAVATOR IMMEDIATELY

            d_In.add(new ArcIn(pTransToCrush20, tMoveCrush20, 1));
            d_Out.add(new ArcOut(tMoveCrush20, pWaitFrom20, 1));

            d_In.add(new ArcIn(pWaitFrom20, tUnload20, 1));
            d_In.add(new ArcIn(freeCrusher, tUnload20, 1));
            d_Out.add(new ArcOut(tUnload20, pTransToExc20, 1));
            d_Out.add(new ArcOut(tUnload20, freeCrusher, 1));

            d_In.add(new ArcIn(pTransToExc20, tMoveExc20, 1));
            d_Out.add(new ArcOut(tMoveExc20, pWaitExc20, 1)); // Truck arrives back in queue

            // --- Arcs (50t) ---
            d_In.add(new ArcIn(pWaitExc50, tLoad50, 1));
            d_In.add(new ArcIn(pFreeExc, tLoad50, 1)); // Seize excavator
            d_Out.add(new ArcOut(tLoad50, pTransToCrush50, 1)); // Truck leaves
            d_Out.add(new ArcOut(tLoad50, pFreeExc, 1)); // RELEASE EXCAVATOR IMMEDIATELY

            d_In.add(new ArcIn(pTransToCrush50, tMoveCrush50, 1));
            d_Out.add(new ArcOut(tMoveCrush50, pWaitFrom50, 1));

            d_In.add(new ArcIn(pWaitFrom50, tUnload50, 1));
            d_In.add(new ArcIn(freeCrusher, tUnload50, 1));
            d_Out.add(new ArcOut(tUnload50, pTransToExc50, 1));
            d_Out.add(new ArcOut(tUnload50, freeCrusher, 1));

            d_In.add(new ArcIn(pTransToExc50, tMoveExc50, 1));
            d_Out.add(new ArcOut(tMoveExc50, pWaitExc50, 1)); // Truck arrives back in queue
        }

        net = new PetriNet("ExcavatorsAndCrusher", d_P, d_T, d_In, d_Out);
        PetriP.initNext();
        PetriT.initNext();
        ArcIn.initNext();
        ArcOut.initNext();
    }
}