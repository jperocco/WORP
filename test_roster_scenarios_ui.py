import unittest
from streamlit.testing.v1 import AppTest

SCRIPT='''
import streamlit as st
from worp_roster_scenarios import render_roster_scenarios
from test_roster_scenarios import ENV,SLOTS
league=st.selectbox('Test league',['A','B'])
render_roster_scenarios(ENV,24,SLOTS,league,{})
'''


class ScenarioUITests(unittest.TestCase):
    def test_edit_save_compare_and_league_isolation(self):
        app=AppTest.from_string(SCRIPT).run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(app.button[0].disabled)
        amounts={'QB Scoring':3,'RB Scoring':4,'WR Scoring':5,'TE Scoring':3,
                 'QB Extra':2,'RB Extra':5,'WR Extra':1,'TE Extra':1}
        for widget in app.number_input:widget.set_value(amounts[widget.label])
        app.text_input[0].set_value('Scenario A');app.run()
        self.assertFalse(app.button[0].disabled)
        app.button[0].click().run()
        self.assertEqual(app.dataframe[-1].value.iloc[0]['Total'],24)
        self.assertEqual(app.dataframe[-1].value.iloc[0]['QB Extra'],2)
        app.selectbox[0].set_value('B').run()
        self.assertEqual(len(app.dataframe),1)
        self.assertTrue(app.button[0].disabled)
        app.selectbox[0].set_value('A').run()
        self.assertEqual(app.dataframe[-1].value.iloc[0]['Scenario'],'Scenario A')
        self.assertEqual(len(app.exception),0)

    def test_overallocation_cannot_save(self):
        app=AppTest.from_string(SCRIPT).run()
        app.number_input[0].set_value(24)
        app.number_input[1].set_value(1)
        app.text_input[0].set_value('Too many');app.run()
        self.assertTrue(app.button[0].disabled)
        self.assertTrue(any('Remove 1' in x.value for x in app.warning))


if __name__=='__main__':unittest.main()
