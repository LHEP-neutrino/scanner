//used in the plots.C file
float tilesizex = 300;
float tilesizey = 500;
float n_y = 25;//100;//33;//25;//number of measurements for y direction; high res (5mm): 100; 2cm steps: 25; 1cm steps: 50
float y_max = tilesizey;//length in y direction
float n_x = 15;//60;//20//15;//number of measurements for x direction High res (5mm): 60; 2cm steps: 15; 1cm steps: 30

float cut_x_min = 100;
float cut_x_max = 200;
float cut_y_min = 360;
float cut_y_max = 460;

Float_t sum_and_error[2];
//Sum of an array
Float_t arr_sum(Float_t arr[], int n)
{
    Float_t  sum = 0; // initialize sum
 
    // Iterate through all elements
    // and add them to sum
    for (int i = 0; i < n; i++)
    sum += arr[i];
 
    return sum;
}

Float_t *tile_plot(const char* rootfilename,const float mean_of_all_monitors){
	bool scan_no_cor = false; //scan without correction
	bool mon_only = false; //monitoring points only, not dependent on step
	bool sipm_no_cor = false; //each SiPM individual plotted
	bool correction = true; //monitoring compared to the step, make linear fit and do the scan plot but corrected and corrected SiPm individual
	
	float C; //const to which all the values will be adjusted
	float factor; //this is the correction to put all of the Tiles on the same level
	Float_t sum;
	Float_t sum_error;
	
	
	TFile* f_in = new TFile(rootfilename,"READ");
	TTree* t_out = (TTree*)f_in->Get("t_out");


	TString strFullpath = TString("/home/lhep/ArCLight_3DScan/scan_ACLFSD_1/scan_plots_new_setup2_RnD/")+TString(string(rootfilename).substr(0,string(rootfilename).size()-5))+TString("/");
	
	gSystem->MakeDirectory(strFullpath);

	if(scan_no_cor){
		//Canvas Labeling
		TCanvas* Scan = new TCanvas("Scan"+TString(rootfilename),"Scan plot "+TString(rootfilename),3000,3000);
		Scan->cd();
		
		//create Histogram
		TH2F* h = new TH2F("h"+TString(rootfilename),"3D Scan "+TString(rootfilename), n_x,0,300,n_y,0,y_max);
		t_out->Project("h"+TString(rootfilename),"y:x","LY_tot_nph"); //y<300 so that the monitor is not shown
		h->SetTitle(Form("Light per point %s;x-position;y-position",rootfilename));
		gStyle->SetOptStat("");
		h->Draw("colz");
		Scan->SaveAs(TString(strFullpath)+TString("scan_no_cor_all_tiles")+TString(".png"));
	}

	if(sipm_no_cor){
		//Canvas Labeling
		TCanvas* Scan_s = new TCanvas("Scan_s"+TString(rootfilename),"Scan plot for each SiPM "+TString(rootfilename),3000,3000);
		Scan_s->DivideSquare(6,0.01,0.01,0);
		Scan_s->cd();

		//create Histogram
		for(int i=0;i<6;i++){
			Scan_s->cd(i+1);
			TH2F* h = new TH2F(Form("h%d",i)+TString(rootfilename),"3D Scan SiPMs "+TString(rootfilename), n_x,0,300,n_y,0,y_max);
			t_out->Project(Form("h%d",i)+TString(rootfilename),"y:x",Form("LY_nph[%d]",i)); 
			h->SetTitle(Form("Light per point for SiPM %d in %s;x-position;y-position",i+1,rootfilename));
			h->Draw("colz");
		}
		Scan_s->SaveAs(TString(strFullpath)+TString("scan_SiPM_no_cor_all_tiles")+TString(".png"));
	}

	if(mon_only){
		//Plot the drift on the monitor
		TCanvas* mon_drift = new TCanvas("mon_drift"+TString(rootfilename),"Drift of the Monitor "+TString(rootfilename),3000,3000);
		mon_drift->cd();
		t_out->Draw(Form("LY_tot_mon_nph:Entry$>>h_temp%s",rootfilename));
		TH1F *h_mon = (TH1F*)gDirectory->Get("h_temp"+TString(rootfilename));
		h_mon->SetMarkerStyle(20);
		h_mon->SetTitle(Form("Drift on the monitor %s;step;number of photoelectrons",rootfilename));
		gStyle->SetOptStat("");
		h_mon->Draw();
		mon_drift->SaveAs(TString(strFullpath)+TString("monitor_drift_no_fit_all_tiles")+TString(".png"));
	}

	if(correction){
		//Make linear fit
		//Plot the drift on the monitor per step
		TCanvas* mon_d = new TCanvas("mon_d"+TString(rootfilename),"Drift of the Monitor Linear Fit "+TString(rootfilename),3000,3000);
		mon_d->cd();
		t_out->Draw(Form("LY_tot_mon_nph:Entry$:LY_tot_mon_nph_rms>>h_temp3%s",rootfilename));//,Form("x>%f && x<%f && y>%f && y<%f ",cut_x_min,cut_x_max,cut_y_min,cut_y_max));
		//t_out->Draw(Form("LY_tot_mon_nph:Entry$>>h_temp3%s",rootfilename),"z<0&&Entry$!=0&&Entry$!=1");
		TGraphErrors *gr_mon = new TGraphErrors(t_out->GetSelectedRows(),t_out->GetV2(),t_out->GetV1(),0,t_out->GetV3());
		TF1 *fitt = new TF1("fitt"+TString(rootfilename),"[0]*x+[1]",0,t_out->GetEntries());
		gr_mon->Fit("fitt"+TString(rootfilename),"W");
		gr_mon->SetMarkerStyle(20);
		gr_mon->SetTitle(Form("Drift on the monitor corresponding to the step %s;step;number of photoelectrons",rootfilename));
		gr_mon->Draw("ap");
		Double_t k = fitt->GetParameter(0);
		Double_t A = fitt->GetParameter(1);

	
	
	
		/*old version:
		//Make linear fit
		//Plot the drift on the monitor per step
		TCanvas* mon_drift_s = new TCanvas("mon_drift_s"+TString(rootfilename),"Drift of the Monitor Linear Fit "+TString(rootfilename),3000,1500);
		mon_drift_s->cd();
		t_out->Draw(Form("LY_tot_mon_nph:Entry$>>h_temp2%s",rootfilename),"z<0&&Entry$!=0");
		TH1F *h_mon_s = (TH1F*)gDirectory->Get("h_temp2"+TString(rootfilename));
		TF1 *fit = new TF1("fit"+TString(rootfilename),"[0]*x+[1]",0,t_out->GetEntries());
		h_mon_s->Fit("fit"+TString(rootfilename));
		h_mon_s->SetMarkerStyle(20);
		h_mon_s->SetTitle(Form("Drift on the monitor corresponding to the step %s;step;number of photoelectrons",rootfilename));
		gStyle->SetOptStat("");
		h_mon_s->Draw();
		Double_t k = fit->GetParameter(0);
		Double_t A = fit->GetParameter(1);
		//Printf("slope: %f und intercept: %f",k,A);
		*/
		
		mon_d->SaveAs(TString(strFullpath)+TString("monitor_drift_step_fit_all_tiles")+TString(".png"));

		C = TMath::Mean(t_out->GetSelectedRows(),t_out->GetV1()); //const to which all the values will be adjusted
		factor = mean_of_all_monitors/C; //this is the correction to put all of the Tiles on the same level

		//Plot the scan with calibrated values
		//Canvas Labeling
		TCanvas* Scan_cor = new TCanvas("Scan_cor"+TString(rootfilename),"Scan plot corrected for all tiles: "+TString(rootfilename),tilesizex*2.1,tilesizex*2.1);
		Scan_cor->cd();
	
		//create Histogram for the corrected values
		TH2F* h_cor = new TH2F("h_cor"+TString(rootfilename),"Scan corrected for all tiles "+TString(rootfilename),5,cut_x_min,cut_x_max,5,cut_y_min,cut_y_max);
		//t_out->Project("h_cor"+TString(rootfilename),"y:x",Form("LY_tot_nph*%f*%f/(LY_tot_mon_nph)*(LY_tot_nph>0 && x>%f && x<%f && y>%f && y<%f)",C,factor,cut_x_min,cut_x_max,cut_y_min,cut_y_max)); //y<300 so that the monitor is not shown
		t_out->Project("h_cor"+TString(rootfilename),"y:x",
		Form("LY_nph[%d]*%f*%f/(LY_tot_mon_nph)+LY_nph[%d]*%f*%f/(LY_tot_mon_nph)*(LY_nph[%d]+LY_nph[%d]>0&& x > %f && x < %f && y > %f && y < %f)", 
		1,C,factor,4,C,factor,1,4,cut_x_min, cut_x_max, cut_y_min, cut_y_max));
		h_cor->SetTitle(Form("Light per point (corrected the mean %f to %f photons for all tiles) %s;x-position;y-position",C,mean_of_all_monitors,rootfilename));
		gStyle->SetOptStat("");
		h_cor->SetMinimum(0);
		h_cor->SetMaximum(30);
		h_cor->Draw("colz");
		Scan_cor->SaveAs(TString(strFullpath)+TString("scan_cor_all_tiles")+TString(".png"));


		//Plot the error of the scan with calibrated values
		//Canvas Labeling
		TCanvas* Scan_cor_e = new TCanvas("Scan_cor_e"+TString(rootfilename),"Scan error plot corrected for all tiles: "+TString(rootfilename),tilesizex*2.1,tilesizex*2.1);
		Scan_cor_e->cd();
		//create Histogram for the error of the corrected values
		TH2F* h_cor_e = new TH2F("h_cor_e"+TString(rootfilename),"3D Scan of the error corrected for all tiles "+TString(rootfilename), 5,cut_x_min,cut_x_max,5,cut_y_min,cut_y_max);
		
		
		//VERBESSERE HIER NOCH DEN FEHELER FÜR DEN MONITOR
		//
		//t_out->Project("h_cor_e"+TString(rootfilename),"y:x",Form("LY_tot_nph_rms*%f*%f/(LY_tot_mon_nph)*(LY_tot_nph>0&& x > %f && x < %f && y > %f && y < %f)", 
        //            C, factor, cut_x_min, cut_x_max, cut_y_min, cut_y_max)); 
		t_out->Project("h_cor_e"+TString(rootfilename),"y:x",
				Form("LY_nph_rms[%d]*%f*%f/(LY_tot_mon_nph)+LY_nph_rms[%d]*%f*%f/(LY_tot_mon_nph)*(LY_nph[%d]+LY_nph[%d]>0&& x > %f && x < %f && y > %f && y < %f)", 
				1,C,factor,4,C,factor,1,4,cut_x_min, cut_x_max, cut_y_min, cut_y_max)); 

		//
		h_cor_e->SetTitle(Form("Light error per point (corrected the mean %f to %f photons for all tiles) %s;x-position;y-position",C,mean_of_all_monitors,rootfilename));
		gStyle->SetOptStat("");
		h_cor_e->Draw("colz");
		//Scan_cor_e->SaveAs(TString(strFullpath)+TString("scan_cor_err_all_tiles")+TString(".png"));

		float_t LY_tot_nph_rms_squ[t_out->GetSelectedRows()];
		for(int i=0;i<t_out->GetSelectedRows();i++){
			LY_tot_nph_rms_squ[i]=t_out->GetW()[i]*t_out->GetW()[i];
			//printf("weight is: %f \n",LY_tot_nph_rms_squ[i]);
		}
		sum_error = sqrt(arr_sum(LY_tot_nph_rms_squ,t_out->GetSelectedRows()));
		printf("Sum error is %f \n", sum_error);

		//calculate the total light (with the sum of all bins)
		int x1 = 0, x2 = h_cor->GetNbinsX();  // x1 = 0, x2 = last bin on x-axis
		int y1 = 0, y2 = h_cor->GetNbinsY();  // y1 = 0, y2 = last bin on y-axis

		sum = h_cor->Integral(x1,x2,y1,y2);
		printf("The sum is: %f \n",sum);

		//each SiPM plotted
		//Canvas Labeling
		TCanvas* Scan_s_c = new TCanvas("Scan_s_c"+TString(rootfilename),"Scan plot for each SiPM corrected for all tiles: "+TString(rootfilename),tilesizey*2.1,tilesizex*2.1);
		Scan_s_c->Divide(2,1,0.01,0.01);
		Scan_s_c->cd();

		//create Histogram
		for(int i = 1; i <= 4; i += 3){
			if (i==1){
				Scan_s_c->cd(2);}
			else {
				Scan_s_c->cd(1);}
			TH2F* h_c = new TH2F(Form("h_c%d%s",i,rootfilename),Form("3D Scan SiPMs corrected mean %f to %f: %s",C,mean_of_all_monitors,rootfilename), 5,cut_x_min,cut_x_max,5,cut_y_min,cut_y_max);
			t_out->Project(Form("h_c%d%s",i,rootfilename),"y:x",Form("LY_nph[%d]*%f*%f/(LY_tot_mon_nph)*(LY_nph[%d]>0&& x > %f && x < %f && y > %f && y < %f)",i,C,factor,i,cut_x_min, cut_x_max, cut_y_min, cut_y_max));
			h_c->SetTitle(Form("Light per point for SiPM %d corrected mean  %f to %f photons: %s;x-position;y-position",i+1,C,mean_of_all_monitors,rootfilename));
			h_c->SetMinimum(0);
			h_c->SetMaximum(50);
			h_c->Draw("colz");
		}
		Scan_s_c->SaveAs(TString(strFullpath)+TString("scan_SiPM_cor_all_tiles")+TString(".png"));
	}

	sum_and_error[0]=sum;
	sum_and_error[1]=sum_error;	

	// Do The LY over distance for each x position!! 
	//plot the light over distance for a tile
	TCanvas* Scan_cor_distance = new TCanvas("Scan_distance"+TString(rootfilename),"Scan plot corrected for all tiles over distance: "+TString(rootfilename),tilesizex*2.1,tilesizex*2.1);
	Scan_cor_distance->cd();


	// Define variables for tree branches
	float_t x, y, LY_tot_mon_nph;
	float_t LY[6];
	t_out->SetBranchAddress("x", &x);
	t_out->SetBranchAddress("y", &y);
	t_out->SetBranchAddress("LY_nph", &LY);
	t_out->SetBranchAddress("LY_tot_mon_nph", &LY_tot_mon_nph);
	Long64_t nEntries = t_out->GetEntries();


	// Loop over tree entries to fill TGraph
	float_t x_ar[] = {110,130,150,170,190};
	int color_palette[] = {kRed, kBlue, kGreen, kMagenta, kOrange};  

	std::map<int, TGraph*> graphs;
	for (int i = 0; i < 5; i++) {
		graphs[x_ar[i]] = new TGraph();
		graphs[x_ar[i]]->SetMarkerColor(color_palette[i]);
		graphs[x_ar[i]]->SetMarkerStyle(34);
		//graphs[x_ar[i]]>SetMarkerSize(2.0);
	}

	for (Long64_t i = 0; i < nEntries; i++) {
		t_out->GetEntry(i);

		// Apply cut: Only add points with valid LY_nph values
		if (LY[1] + LY[4] > 0 && x > cut_x_min && x < cut_x_max && y > cut_y_min && y < cut_y_max ) {
			Double_t correctedLY = (LY[1] * C * factor + LY[4] * C * factor) / LY_tot_mon_nph;

			if (graphs.find(x) != graphs.end()) {
				graphs[x]->SetPoint(graphs[x]->GetN(), y, correctedLY);
			}
		}
	}


	TLegend *legend = new TLegend(0.1, 0.7, 0.2, 0.9);
	for (int i = 0; i < 5; i++) {
		if (graphs[x_ar[i]]->GetN() > 0) {  // Only add graphs with points
			legend->AddEntry(graphs[x_ar[i]], Form("X = %d", int(x_ar[i])), "p");
		}
	}

	// Set graph title
	//g_cor_distance->SetTitle(Form("Light per point (corrected to %f photons);Y-position;p.e.", mean_of_all_monitors));

	// Draw the graph
	gStyle->SetOptStat(0);
	//g_cor_distance->Draw("AP");  // "A" for axis, "P" for points
	// Draw all graphs
	gPad->Update();
	graphs.begin()->second->Draw("AP"); // Draw first graph with axis
	graphs.begin()->second->GetYaxis()->SetRangeUser(0, 80);
	for (auto &entry : graphs) {
    	entry.second->Draw("P SAME");
	}
	legend->Draw();
	Scan_cor_distance->Update();


	Scan_cor_distance->SaveAs(TString(strFullpath)+TString("scan_cor_LY_drop_each_x")+TString(".png"));





	return sum_and_error;
}
