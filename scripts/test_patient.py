import sys
from pathlib import Path
# ensure project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from schemas import Patient

p = Patient(id='P001', name='Ritish', city='Chandigarh', age=23, gender='male', height=1.77, weight=65.0, disease_injury='flu')
print('bmi=', p.bmi, 'verdict=', p.verdict)
