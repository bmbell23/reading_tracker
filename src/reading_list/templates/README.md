# Templates Directory Structure

├── email/                                  # Email notification templates
├── excel/                                  # Excel import/export templates
├── reports/                                # Report generation templates
│   ├── chain/                              # Reading chain (TBR) related templates
│   │   ├── reading_chain.html
│   │   └── reading_chain_report.html
│   ├── projected/                          # Projected reading templates
│   │   ├── projected_reading_report.html
│   │   └── projected_readings.html
│   └── yearly/                             # Yearly report templates
│       └── yearly_reading_report.html      
├── tbr/                                    # To-be-read management templates
│   ├── index.html                          # Main index page for TBR manager
│   └── tbr_manager.html                    # Interactive TBR manager interface
└── styles/                                 # Shared CSS styles
    ├── base.css                            # Base styles for all templates
    ├── reports.css                         # Styles specific to reports
    ├── tbr_manager.css                     # Styles for the TBR manager
    └── yearly_report.css                   # Styles for yearly reports
