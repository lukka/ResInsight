/////////////////////////////////////////////////////////////////////////////////
//
//  Copyright (C) 2017-     Statoil ASA
// 
//  ResInsight is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
// 
//  ResInsight is distributed in the hope that it will be useful, but WITHOUT ANY
//  WARRANTY; without even the implied warranty of MERCHANTABILITY or
//  FITNESS FOR A PARTICULAR PURPOSE.
// 
//  See the GNU General Public License at <http://www.gnu.org/licenses/gpl.html> 
//  for more details.
//
/////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "Rim3dOverlayInfoConfig.h"

#include "RifReaderEclipseSummary.h"

#include "cafPdmPointer.h"

#include <QDialog>

class QLabel;
class QRadioButton;
class QLineEdit;
class QTextEdit;
class QDialogButtonBox;
class QPushButton;
class QMainWindow;
class QListWidget;
class QGridLayout;
class QCheckBox;
class QGroupBox;
class RicSummaryCaseRestartDialogResult;

//==================================================================================================
///  
//==================================================================================================
class RicSummaryCaseRestartDialog : public QDialog
{
    Q_OBJECT

public:
    enum ImportOptions { IMPORT_ALL, SEPARATE_CASES, NOT_IMPORT };

    RicSummaryCaseRestartDialog(QWidget* parent);
    ~RicSummaryCaseRestartDialog();

    static RicSummaryCaseRestartDialogResult    openDialog(const QString& summaryHeaderFile,
                                                           bool showApplyToAllWidget,
                                                           bool buildGridCaseFileList,
                                                           ImportOptions defaultSummaryImportOption,
                                                           ImportOptions defaultGridImportOption,
                                                           RicSummaryCaseRestartDialogResult *lastResult = nullptr,
                                                           QWidget *parent = nullptr);

    ImportOptions                               selectedSummaryImportOption() const;
    ImportOptions                               selectedGridImportOption() const;
    bool                                        applyToAllSelected() const;

private:
    void                                        populateFileList(QGridLayout* gridLayout, const std::vector<RifRestartFileInfo>& fileInfos);
    void                                        appendFileInfoToGridLayout(QGridLayout* gridLayout, const RifRestartFileInfo& fileInfo);
    RifRestartFileInfo                          getFileInfo(const QString& summaryHeaderFile);
    void                                        displayWarningsIfAny(const QStringList& warnings);

private slots:
    void slotDialogOkClicked();
    void slotDialogCancelClicked();

private:
    QGroupBox*                          m_currentFilesGroup;
    QGridLayout*                        m_currentFilesLayout;

    QGridLayout*                        m_summaryFilesLayout;

    QRadioButton*                       m_summaryReadAllBtn;
    QRadioButton*                       m_summarySeparateCasesBtn;
    QRadioButton*                       m_summaryNotReadBtn;

    QGroupBox*                          m_gridFilesGroup;
    QGridLayout*                        m_gridFilesLayout;

    QRadioButton*                       m_gridNotReadBtn;
    QRadioButton*                       m_gridSeparateCasesBtn;

    QCheckBox*                          m_applyToAllCheckBox;
    QDialogButtonBox*                   m_buttons;

    QListWidget*                        m_warnings;
};


//==================================================================================================
///  
//==================================================================================================
class RicSummaryCaseRestartDialogResult
{
public:
    RicSummaryCaseRestartDialogResult() :
        ok(false),
        summaryImportOption(RicSummaryCaseRestartDialog::IMPORT_ALL),
        gridImportOption(RicSummaryCaseRestartDialog::NOT_IMPORT),
        applyToAll(false) {}

    RicSummaryCaseRestartDialogResult(bool _ok,
                                      RicSummaryCaseRestartDialog::ImportOptions _summaryImportOption,
                                      RicSummaryCaseRestartDialog::ImportOptions _gridImportOption,
                                      QStringList _summaryFiles,
                                      QStringList _gridFiles,
                                      bool _applyToAll) :
        ok(_ok),
        summaryImportOption(_summaryImportOption),
        gridImportOption(_gridImportOption),
        summaryFiles(_summaryFiles),
        gridFiles(_gridFiles),
        applyToAll(_applyToAll)
    {
    }

    bool                                                ok;
    RicSummaryCaseRestartDialog::ImportOptions          summaryImportOption;
    RicSummaryCaseRestartDialog::ImportOptions          gridImportOption;
    QStringList                                         summaryFiles;
    QStringList                                         gridFiles;
    bool                                                applyToAll;
};