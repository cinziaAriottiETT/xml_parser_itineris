#!/usr/bin/env python3
"""
Validatore XML per il modello ITINERIS IT-IOOS Metadata Model
Verifica che i file XML rispettino la struttura e gli attributi richiesti
"""

import xml.etree.ElementTree as ET
import os
import shutil
import sys
from typing import List, Tuple
from datetime import datetime
import re



class XMLValidator:
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
        # Attributi obbligatori per il dataset
        self.required_dataset_attrs = {
            'type', 'datasetID', 'active'
        }
        
        # Attributi obbligatori globali (quelli che non dovrebbero essere "COMPLETARE")
        self.required_global_attrs = {
            'ri_name', 'institution', 'institution_logo', 'ri_short_name'
        }
        
        # Attributi che dovrebbero avere valori specifici
        self.expected_values = {
            'geospatial_vertical_positive': 'down'
        }
        
        # Attributi che dovrebbero avere valori specifici
        self.expected_values_ri_short_name = {
            'JERICO', 'DANUBIUS', 'eLTER'
        }
        
        # Attributi per le variabili
        self.required_attrs = {
            'standard_name', 'long_name', 'units', 'parameter_sdn_name'
        }
        
        # Attributi per le variabili QC
        self.qc_required_attrs = {
            'standard_name', 'long_name', 'flag_meanings', 'flag_values'
        }
        
    def validate_xml_file(self, xml_path: str) -> Tuple[bool, List[str], List[str]]:

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            self._validate_global_attributes(root, xml_path)
            self._validate_data_variables(root, xml_path)
            
        except ET.ParseError as e:
            self.errors.append(f"Errore di parsing XML: {e}")
        except FileNotFoundError:
            self.errors.append(f"File non trovato: {xml_path}")
        except Exception as e:
            self.errors.append(f"Errore generico: {e}")
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors.copy(), self.warnings.copy()
    
    def _validate_global_attributes(self, root: ET.Element, xml_path: str):
        add_attrs = root.find('addAttributes')
        if add_attrs is None:
            self.errors.append("Nodo 'addAttributes' mancante nel root")
            root.append(ET.Comment(" ATTENZIONE: manca il nodo addAttributes nel root "))
            ET.ElementTree(root).write(xml_path, encoding='utf-8')
            return
        
        attrs_dict = {}
        for att in add_attrs.findall('att'):
            name = att.get('name')
            value = att.text or ''
            attrs_dict[name] = value
        
        for attr in self.required_global_attrs:
            if attr not in attrs_dict:
                add_attrs.append(ET.Comment(f" Manca attributo obbligatorio: {attr} "))
        
        for attr, expected_value in self.expected_values.items():
            if attr in attrs_dict and attrs_dict[attr] != expected_value:
                self.errors.append(f"Valore errato per '{attr}': atteso '{expected_value}', trovato '{attrs_dict[attr]}'")
        
        for attr in self.required_global_attrs:
            if attr in attrs_dict and attr == 'ri_short_name':
                if attrs_dict[attr] not in self.expected_values_ri_short_name:
                    self.errors.append(f"Valore errato per '{attr}': trovato '{attrs_dict[attr]}'")
        
        ET.ElementTree(root).write(xml_path, encoding='utf-8')

    def _validate_data_variables(self, root: ET.Element, xml_path: str):
        data_vars = root.findall('dataVariable')
        
        for i, var in enumerate(data_vars):
            var_name = f"dataVariable[{i}]"
            source_name = var.find('sourceName')
            
            add_attrs = var.find('addAttributes')
            if add_attrs is None:
                var.append(ET.Comment(f" ATTENZIONE: manca il nodo addAttributes in {var_name} "))
                ET.ElementTree(root).write(xml_path, encoding='utf-8')
                continue
            
            is_qc_var = (source_name is not None and 
                        source_name.text and 
                        '_QC' in source_name.text)
            
            if is_qc_var:
                self._validate_qc_variable(var, var_name, xml_path, root)
            else:
                self._validate_regular_variable(var, var_name, xml_path, root)
    
    def _validate_qc_variable(self, var: ET.Element, var_name: str, xml_path: str, root: ET.Element):
        add_attrs = var.find('addAttributes')
        if add_attrs is None:
            return
        
        attrs_dict = {}
        for att in add_attrs.findall('att'):
            name = att.get('name')
            value = att.text or ''
            attrs_dict[name] = value
        
        for attr in self.qc_required_attrs:
            if attr not in attrs_dict:
                add_attrs.append(ET.Comment(f"Manca attributo obbligatorio '{attr}' "))
        
        ET.ElementTree(root).write(xml_path, encoding='utf-8')

    def _validate_regular_variable(self, var: ET.Element, var_name: str, xml_path: str, root: ET.Element):
        add_attrs = var.find('addAttributes')
        if add_attrs is None:
            return
        
        attrs_dict = {}
        for att in add_attrs.findall('att'):
            name = att.get('name')
            value = att.text or ''
            attrs_dict[name] = value
        
        important_attrs = ['standard_name', 'long_name', 'units']
        for attr in important_attrs:
            if attr not in attrs_dict:
                add_attrs.append(ET.Comment(f"Manca attributo raccomandato '{attr}' "))
            elif attrs_dict[attr] == 'COMPLETARE':
                self.warnings.append(f"{var_name}: attributo '{attr}' non completato")
        
        ET.ElementTree(root).write(xml_path, encoding='utf-8')

    # def validate_xml_file(self, xml_path: str) -> Tuple[bool, List[str], List[str]]:
    #     """
    #     Valida un file XML
        
    #     Args:
    #         xml_path: Percorso del file XML da validare
            
    #     Returns:
    #         Tuple con (is_valid, errors, warnings)
    #     """
    #     self.errors = []
    #     self.warnings = []
        
    #     try:
    #         # Parsing del file XML
    #         tree = ET.parse(xml_path)
    #         root = tree.getroot()
            

    #         # Validazione degli attributi globali
    #         self._validate_global_attributes(root)
            
    #         # Validazione delle variabili
    #         self._validate_data_variables(root)
            
    #     except ET.ParseError as e:
    #         self.errors.append(f"Errore di parsing XML: {e}")
    #     except FileNotFoundError:
    #         self.errors.append(f"File non trovato: {xml_path}")
    #     except Exception as e:
    #         self.errors.append(f"Errore generico: {e}")
        
    #     is_valid = len(self.errors) == 0
    #     return is_valid, self.errors.copy(), self.warnings.copy()



    # def _validate_global_attributes(self, root: ET.Element):
    #     """Valida gli attributi globali"""
    #     add_attrs = root.find('addAttributes')
    #     if add_attrs is None:
    #         return
        
    #     attrs_dict = {}
    #     for att in add_attrs.findall('att'):
    #         name = att.get('name')
    #         value = att.text or ''
    #         attrs_dict[name] = value
        
    #     # Verifica attributi obbligatori
    #     for attr in self.required_global_attrs:
    #         if attr not in attrs_dict:
    #             self.errors.append(f"Attributo globale mancante: {attr}")
    #         elif attr == 'ri_short_name':
    #             if attrs_dict[attr] not in self.expected_values_ri_short_name:
    #                 self.errors.append(f"Valore errato per '{attr}': trovato '{attrs_dict[attr]}'")
        
    #     # Verifica valori attesi
    #     for attr, expected_value in self.expected_values.items():
    #         if attr in attrs_dict and attrs_dict[attr] != expected_value:
    #             self.errors.append(f"Valore errato per '{attr}': atteso '{expected_value}', trovato '{attrs_dict[attr]}'")
                

    # def _validate_data_variables(self, root: ET.Element):
    #     """Valida le variabili dati"""
    #     data_vars = root.findall('dataVariable')
        
    #     for i, var in enumerate(data_vars):
    #         var_name = f"dataVariable[{i}]"
    #         source_name = var.find('sourceName')
            
    #         # Verifica addAttributes per la variabile
    #         add_attrs = var.find('addAttributes')
    #         if add_attrs is None:
    #             self.errors.append(f"{var_name}: elemento 'addAttributes' mancante")
    #             continue
            
    #         # Controlla se è una variabile QC
    #         is_qc_var = (source_name is not None and 
    #                     source_name.text and 
    #                     '_QC' in source_name.text)
            
    #         if is_qc_var:
    #             self._validate_qc_variable(var, var_name)
    #         else:
    #             self._validate_regular_variable(var, var_name)

    # def _validate_qc_variable(self, var: ET.Element, var_name: str):
    #     """Valida una variabile QC"""
    #     add_attrs = var.find('addAttributes')
    #     if add_attrs is None:
    #         return
        
    #     attrs_dict = {}
    #     for att in add_attrs.findall('att'):
    #         name = att.get('name')
    #         value = att.text or ''
    #         attrs_dict[name] = value
        
    #     # Verifica attributi obbligatori per QC
    #     for attr in self.qc_required_attrs:
    #         if attr not in attrs_dict:
    #             self.errors.append(f"{var_name} (QC): attributo mancante '{attr}'")
    #         elif attrs_dict[attr] == 'COMPLETARE':
    #             self.warnings.append(f"{var_name} (QC): attributo '{attr}' non completato")

    # def _validate_regular_variable(self, var: ET.Element, var_name: str):
    #     """Valida una variabile regolare"""
    #     add_attrs = var.find('addAttributes')
    #     if add_attrs is None:
    #         return
        
    #     attrs_dict = {}
    #     for att in add_attrs.findall('att'):
    #         name = att.get('name')
    #         value = att.text or ''
    #         attrs_dict[name] = value
        
    #     # Verifica attributi importanti
    #     important_attrs = ['standard_name', 'long_name', 'units']
    #     for attr in important_attrs:
    #         if attr not in attrs_dict:
    #             self.warnings.append(f"{var_name}: attributo raccomandato mancante '{attr}'")
    #         elif attrs_dict[attr] == 'COMPLETARE':
    #             self.warnings.append(f"{var_name}: attributo '{attr}' non completato")

    # def _is_valid_date(self, date_str: str) -> bool:
    #     """Verifica se una stringa è una data valida"""
    #     date_formats = [
    #         '%Y-%m-%d',
    #         '%Y-%m-%dT%H:%M:%S',
    #         '%Y-%m-%dT%H:%M:%SZ',
    #         '%Y-%m-%dT%H:%M:%S.%fZ'
    #     ]
        
    #     for fmt in date_formats:
    #         try:
    #             datetime.strptime(date_str, fmt)
    #             return True
    #         except ValueError:
    #             continue
    #     return False

    # def _is_valid_url(self, url: str) -> bool:
    #     """Verifica se una stringa è un URL valido"""
    #     url_pattern = re.compile(
    #         r'^https?://'  # http:// or https://
    #         r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    #         r'localhost|'  # localhost...
    #         r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    #         r'(?::\d+)?'  # optional port
    #         r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    #     return url_pattern.match(url) is not None


def main():
    """Funzione principale per l'esecuzione da riga di comando"""
    if len(sys.argv) < 4:
        print("Uso: python validator.py <folder with xml file> <folder for incorrect file> <folder for correct file>")
        sys.exit(1)
    
    validator = XMLValidator()
    
    folder_to_check = sys.argv[1]
    error_folder = sys.argv[2]
    valid_folder = sys.argv[3]
    
    
    
    print('arg: ', sys.argv[2])
    
    for xml_file in os.listdir(folder_to_check):
        xml_file_path = os.path.join(folder_to_check, xml_file)
        if os.path.isfile(xml_file_path):
            print(f"\n{'='*50}")
            print(f"Validazione: {xml_file_path}")
            print(f"{'='*50}")
            
            is_valid, errors, warnings = validator.validate_xml_file(xml_file_path)
            
            if errors:
                print(f"\n❌ ERRORI ({len(errors)}):")
                for error in errors:
                    print(f"  • {error}")
            
            if warnings:
                print(f"\n⚠️  AVVERTIMENTI ({len(warnings)}):")
                for warning in warnings:
                    print(f"  • {warning}")
            
            if is_valid:
                xml_file_valid_path = os.path.join(valid_folder, xml_file)
                shutil.move(xml_file_path, xml_file_valid_path)
            else:
                xml_file_error_path = os.path.join(error_folder, xml_file)
                shutil.move(xml_file_path, xml_file_error_path)
            
            print(f"\nRiepilogo: {len(errors)} errori, {len(warnings)} avvertimenti")


if __name__ == "__main__":
    main()
