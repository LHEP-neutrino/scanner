
#include <TFile.h>
#include <TTree.h>
#include <TH2F.h>
#include <TCanvas.h>
#include <TString.h>
#include <iostream>
#include <fstream>

//const char* files[]={"stability_test_3_s200_stabConv.root"};
const char* files[]={"stability_test_3_s200_stabConv.root","stability_pulse_scan_stabConv.root","stability_pulse_scan_5_stabConv.root","stability_pulse_frequency_scan_1_stabConv.root"};
float C[2];
float D[2];
//path of the data
TString data_path = {"/data/3dscan/root_files/"};

float gain_monitor = 250.18;
float gain_SiPM = 256.66;


float *getMeanMon(const char* rootfilename){
        //get the mean of the monitoring

        TFile* f_in = new TFile(rootfilename,"READ");
        TTree* t_out = (TTree*)f_in->Get("t_out");

        //Make linear fit
        //Plot the drift on the monitor per step
        TCanvas* mon_drift_s = new TCanvas("mon_drift_s","Mean",3000,1500);
        mon_drift_s->cd();
        t_out->Draw("LY_mon_nph:Entry$>>h_temp1");
        C[0] = TMath::Mean(t_out->GetSelectedRows(),t_out->GetV1()); //get the mean
        float stdDev = TMath::RMS(t_out->GetSelectedRows(),t_out->GetV1()); //get the std deviation
        C[1] = stdDev/sqrt(t_out->GetSelectedRows()); //calculate the error
        mon_drift_s->Destructor();
        return C;
}
float *getMeanLRSCompare(const char* rootfilename){
        //get the mean of the monitoring

        TFile* f_in = new TFile(rootfilename,"READ");
        TTree* t_out = (TTree*)f_in->Get("t_out");

        //Plot the drift on the monitor per step
        TCanvas* lrs_drift_s = new TCanvas("lrs_drift_s","LY SiPM-Monitoring SiPM",3000,1500);
        lrs_drift_s->cd();
        t_out->Draw("(LY_nph[2]-LY_mon_nph)/LY_nph[2]:Entry$>>h_temp2");
	
	// Zugriff auf das Histogrammobjekt
	TH2F *h_temp2 = (TH2F*)gDirectory->Get("h_temp2");
	// Ändern der Marker-Stile für die Punkte im Plot
	h_temp2->SetMarkerStyle(5); // Hier setze ich den Marker-Stil auf Quadrat (21), aber du kannst den gewünschten Stil wählen
	h_temp2->GetXaxis()->SetTitle("file number"); // Setze die Beschriftung der x-Achse
	h_temp2->GetYaxis()->SetTitle("(Mean LY SiPM - Mean LY Monitor SiPM)/(Mean LY SiPM)");
	h_temp2->SetTitle("Difference of the LY's");
	gStyle->SetOptStat(0);

	 // Passe die Achsenlimits an
        //h_temp2->GetXaxis()->SetRangeUser(-2, 2); // Setze die x-Achsenlimits auf -2 bis 2
        h_temp2->GetYaxis()->SetRangeUser(0, 4); // Setze die y-Achsenlimits auf 0 bis 2000


	h_temp2->Draw();	
        //h_temp3->Draw();
        lrs_drift_s->Draw();
	lrs_drift_s->SaveAs("stability_plots/"+TString(rootfilename)+"Mean_LY_nph-Mean_LY_mon_nph_vs_entry.png");



        D[0] = TMath::Mean(t_out->GetSelectedRows(),t_out->GetV1()); //get the mean
        float stdDev = TMath::RMS(t_out->GetSelectedRows(),t_out->GetV1()); //get the std deviation
        D[1] = stdDev/sqrt(t_out->GetSelectedRows()); //calculate the error
        //mon_drift_s->Destructor();
        return D;
}

void drawComparisonHistogram(const char* logfilename) {
    // Öffne das Log-Datei und lese die Dateinamen der ROOT-Dateien ein
    std::ifstream infile(logfilename);
    //std::string logFilePath(logfilename);
    //std::string logDir = logFilePath.substr(0, logFilePath.find_last_of("/\\"));
    std::string rootFilePath;
    TCanvas* canvas = new TCanvas("canvas", "canvas",3000,1500);
    //TH2F* h_comparison = new TH2F("h_comparison", "Comparison of the LYs", 15000, 5000, 20000, 15000, 1000, 16000);

    TH2F* h_comparison = new TH2F("h_comparison", "Comparison of the LYs", 100, 0, 350, 100, 0, 350);
    
    TCanvas* canvas_c = new TCanvas("canvas_c", "canvas",3000,1500);
    TH1F* h_dif = new TH1F("h_dif", "Difference of the LYs", 100, -50, 50);

    string scan_name = string(logfilename).substr(0,string(logfilename).size()-4);


    int j = 0;
    std::string line;
    while (std::getline(infile, line)) {
        // Teile die Zeile nach dem letzten Leerzeichen
        std::istringstream iss(line);
        std::vector<std::string> tokens;
        std::string token;
        while (std::getline(iss, token, ' ')) {
            tokens.push_back(token);
        }
        if (tokens.size() < 2) {
            // Wenn die Zeile nicht die erwartete Struktur hat, überspringe sie
            continue;
        }
        rootFilePath = tokens.back(); // Verwende nur das letzte Element (Dateiname)


        // Konstruiere den vollständigen Pfad zur ROOT-Datei
        TString fullRootFilePath = TString(data_path) + TString(scan_name)+TString("/rlog_") + TString(rootFilePath.c_str()).ReplaceAll(".log", "") + ".root";

        // Öffne die ROOT-Datei und lade den TTree
        TFile* file = TFile::Open(fullRootFilePath);
        if (!file || file->IsZombie()) {
            std::cout << "Could not open file: " << fullRootFilePath << std::endl;
            continue;
        }
        TTree* tree = (TTree*)file->Get("rlog");
        if (!tree) {
            std::cout << "Could not find tree in file: " << fullRootFilePath << std::endl;
            file->Close();
            continue;
        }

        // Fülle das Histogramm für den Vergleich von integral.ch04 und integral.ch12
        tree->Draw("integral.ch04:integral.ch12", "", "goff");
        int nEntries = tree->GetSelectedRows();
	//printf("File: " + TString(rootFilePath.c_str()).ReplaceAll(".log", "") +" entries:" + nEntries +"\n");
        double* integral_ch12 = tree->GetV2();
        double* integral_ch04 = tree->GetV1();
        for (int i = 0; i < nEntries; ++i) {
	    //if(integral_ch12[i] - integral_ch04[i]>30000){
            h_comparison->Fill(integral_ch12[i]/gain_SiPM, integral_ch04[i]/gain_monitor);
            h_dif -> Fill((integral_ch12[i]/gain_SiPM - integral_ch04[i]/gain_monitor)/(integral_ch12[i]/gain_SiPM));
	    j = j+1;
	    //cout<<"Measurements "<<i<<" Value: "<< integral_ch12[i] <<" " << integral_ch04[i] <<"\n";
	    //}
        }

        // Schließe die Datei
        file->Close();
    }

    // Setze den Marker-Stil auf 20 (Kreis)
    h_comparison->SetMarkerStyle(5);

    // Setze den Titel und die Achsenbeschriftungen
    h_comparison->SetTitle("Comparison of the LYs for each measurement");
    h_comparison->GetXaxis()->SetTitle("LY SiPM");
    h_comparison->GetYaxis()->SetTitle("LY Monitoring SiPM");

    // Zeige das Histogramm an
    canvas->cd();
    //h_comparison->Draw("colz");
    h_comparison->Draw();
    canvas->SaveAs("stability_plots/"+TString(logfilename)+"crosses_LY_SiPM_vs_LY_mon_SiPM.png");
    // Setze den Marker-Stil auf 20 (Kreis)
    h_dif->SetMarkerStyle(5);

    // Setze den Titel und die Achsenbeschriftungen
    h_dif->SetTitle("Difference of the LYs for each measurement");
    h_dif->GetYaxis()->SetTitle("#");
    h_dif->GetXaxis()->SetTitle("(LY SiPM - LY Monitoring SiPM)/(LY SiPM)");
    
    cout<<"Measurements "<<j<<"\n";

    // Zeige das Histogramm an
    canvas_c->cd();
    h_dif->Draw();
    canvas_c->SaveAs("stability_plots/"+TString(logfilename)+"_LY_SiPM-LY_mon_SiPM_histogram.png");
    //canvas->Print(Form("%s/comparison_all.png", logDir.c_str())); // Speichere das Histogramm als Bild
}




void getLRSRelation(const char* rootfilename){
        //get the mean of the monitoring

        TFile* f_in = new TFile(rootfilename,"READ");
        TTree* t_out = (TTree*)f_in->Get("t_out");

        //Plot the drift on the monitor per step
        TCanvas* lrs_relation = new TCanvas("lrs_relation","LY SiPM vs Monitoring SiPM",3000,1500);
        lrs_relation->cd();
        t_out->Draw("LY_nph[2]:LY_mon_nph>>h_temp3");
	
	// Zugriff auf das Histogrammobjekt
	TH2F *h_temp3 = (TH2F*)gDirectory->Get("h_temp3");
	// Ändern der Marker-Stile für die Punkte im Plot
	h_temp3->SetMarkerStyle(5); // Hier setze ich den Marker-Stil auf Quadrat (21), aber du kannst den gewünschten Stil wählen
	h_temp3->GetXaxis()->SetTitle("LY Monitor SiPM"); // Setze die Beschriftung der x-Achse
	h_temp3->GetYaxis()->SetTitle("LY SiPM");
	h_temp3->SetTitle("Relation of the LYs means of the different files");
	gStyle->SetOptStat(0);

	h_temp3->Draw();	
        //h_temp3->Draw();
        lrs_relation->Draw();
        lrs_relation->SaveAs("stability_plots/"+TString(rootfilename)+"Mean_LY_SiPM_vs_Mean_LY_mon_SiPM.png");


        return;
}

void getLRSRelation_w_error(const char* rootfilename){
	TFile* f_in = new TFile(rootfilename,"READ");
	TTree* t_out = (TTree*)f_in->Get("t_out");

	// Define variables to hold the data and errors
	Float_t LY_nph[6], LY_mon_nph, LY_nph_rms[6], LY_mon_nph_rms;

	// Set branch addresses
	t_out->SetBranchAddress("LY_nph",&LY_nph);
	t_out->SetBranchAddress("LY_mon_nph", &LY_mon_nph);
	t_out->SetBranchAddress("LY_nph_rms", &LY_nph_rms);
	t_out->SetBranchAddress("LY_mon_nph_rms", &LY_mon_nph_rms);

	// Create a TGraphErrors object
	TGraphErrors *gr_temp3 = new TGraphErrors(t_out->GetEntries());

	// Loop over entries in the TTree to fill the TGraphErrors
	for (int i = 0; i < t_out->GetEntries(); ++i) {
	    t_out->GetEntry(i);
	    float x = LY_mon_nph;
	    float y = LY_nph[2];
	    float ex = LY_mon_nph_rms;
	    float ey = LY_nph_rms[2];
	    gr_temp3->SetPoint(i, x, y); // Set point coordinates
	    gr_temp3->SetPointError(i, ex, ey); // Set point errors
	}

	// Create a canvas
	TCanvas* lrs_relation = new TCanvas("lrs_relation", "LY SiPM vs Monitoring SiPM", 3000, 1500);

	// Set up the plot
	gr_temp3->SetMarkerStyle(5);
	gr_temp3->GetXaxis()->SetTitle("LY Monitor SiPM");
	gr_temp3->GetYaxis()->SetTitle("LY SiPM");
	gr_temp3->SetTitle("Relation of the LYs means of the different files");
	gStyle->SetOptStat(0);

	// Draw the graph
	gr_temp3->Draw("AP");
	lrs_relation->Draw();
	lrs_relation->SaveAs(("stability_plots/" + TString(rootfilename) + "Mean_LY_SiPM_vs_Mean_LY_mon_SiPM.png").Data());

	//delete lrs_relation;
	//delete gr_temp3;
	//delete t_out;
	//delete f_in;
	return;
}

void getLRSRelation_to_Vpulse_w_error(const char* rootfilename){
	TFile* f_in = new TFile(rootfilename,"READ");
	TTree* t_out = (TTree*)f_in->Get("t_out");

	// Define variables to hold the data and errors
	Float_t LY_nph[6], LY_mon_nph, LY_nph_rms[6], LY_mon_nph_rms;

	// Set branch addresses
	t_out->SetBranchAddress("LY_nph",&LY_nph);
	t_out->SetBranchAddress("LY_mon_nph", &LY_mon_nph);
	t_out->SetBranchAddress("LY_nph_rms", &LY_nph_rms);
	t_out->SetBranchAddress("LY_mon_nph_rms", &LY_mon_nph_rms);

	// Create a TGraphErrors object
	TGraphErrors *gr_temp4 = new TGraphErrors(t_out->GetEntries());
	TGraphErrors *gr_temp5 = new TGraphErrors(t_out->GetEntries());

	int pulse_setting = 50;
	// Loop over entries in the TTree to fill the TGraphErrors
	for (int i = 0; i < t_out->GetEntries(); ++i) {
	    t_out->GetEntry(i);
	    float x = LY_mon_nph;
	    float y = LY_nph[2];
	    float ex = LY_mon_nph_rms;
	    float ey = LY_nph_rms[2];
	    gr_temp4->SetPoint(i, pulse_setting, x); // Set point coordinates
	    gr_temp4->SetPointError(i, 0, ex); // Set point errors
	    gr_temp5->SetPoint(i, pulse_setting, y); // Set point coordinates
	    gr_temp5->SetPointError(i, 0, ey); // Set point errors
            pulse_setting = pulse_setting + 1;
	}

	// Create a canvas
	TCanvas* lrs_relation_to_pulse = new TCanvas("lrs_relation_to_pulse", "LY SiPM vs Pulse setting", 3000, 1500);

	TCanvas* lrs_mon_relation_to_pulse = new TCanvas("lrs_mon_relation_to_pulse", "LY monitor SiPM vs Pulse setting", 3000, 1500);

	lrs_mon_relation_to_pulse->cd();
	// Set up the plot
	gr_temp4->SetMarkerStyle(5);
	gr_temp4->GetXaxis()->SetTitle("Pulse setting (-s)(-p 0)");
	gr_temp4->GetYaxis()->SetTitle("LY Monitor SiPM");
	gr_temp4->SetTitle("Relation of the LYs means of the different files for different pulse settings");
	gStyle->SetOptStat(0);

	// Draw the graph
	gr_temp4->Draw("AP");
	lrs_mon_relation_to_pulse->Draw();
	lrs_mon_relation_to_pulse->SaveAs(("stability_plots/" + TString(rootfilename) + "Mean_LY_Monitor_SiPM_vs_pulse_setting.png").Data());


	lrs_relation_to_pulse->cd();
	// Set up the plot
	gr_temp5->SetMarkerStyle(5);
	gr_temp5->GetXaxis()->SetTitle("Pulse setting (-s)(-p 0)");
	gr_temp5->GetYaxis()->SetTitle("LY SiPM");
	gr_temp5->SetTitle("Relation of the LYs means of the different files for different pulse settings");
	gStyle->SetOptStat(0);

	// Draw the graph
	gr_temp5->Draw("AP");
	lrs_relation_to_pulse->Draw();
	lrs_relation_to_pulse->SaveAs(("stability_plots/" + TString(rootfilename) + "Mean_LY_SiPM_vs_pulse_setting.png").Data());

	//delete lrs_relation;
	//delete gr_temp3;
	//delete t_out;
	//delete f_in;
	return;
}



void plot_stability(){	
	const int size_of_files=sizeof(files)/sizeof(files[0]);	
	float_t means[size_of_files];
        float_t errors[size_of_files];
        float_t scan_nr[size_of_files];
	float_t means_lrs[size_of_files];
        float_t errors_lrs[size_of_files];
        Float_t* K;
	Float_t* F;
        //plot the different means of monitoring
        for(int i=0;i<size_of_files;i++){
		F = getMeanLRSCompare(files[i]);
		means_lrs[i] = F[0];
                errors_lrs[i] = F[1];
		getLRSRelation_w_error(files[i]);
	}
	getLRSRelation_to_Vpulse_w_error("stability_pulse_scan_5_stabConv.root");

	drawComparisonHistogram("stability_test_3_s200.log");
	drawComparisonHistogram("stability_pulse_scan.log");
	drawComparisonHistogram("stability_pulse_scan_5.log");
	drawComparisonHistogram("stability_pulse_frequency_scan_1.log");


}

