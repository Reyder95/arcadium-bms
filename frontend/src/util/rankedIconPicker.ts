import UnrankedIcon from '../assets/ranked_icons/Unranked-cropped.png';
import CopperIcon from '../assets/ranked_icons/Copper-cropped.png';
import BronzeIcon from '../assets/ranked_icons/Bronze-cropped.png';
import SilverIcon from '../assets/ranked_icons/Silver-cropped.png';
import GoldIcon from '../assets/ranked_icons/Gold-cropped.png';
import PlatinumIcon from '../assets/ranked_icons/Platinum-cropped.png';
import EmeraldIcon from '../assets/ranked_icons/Emerald-cropped.png';
import DiamondIcon from '../assets/ranked_icons/Diamond-cropped.png';
import MasterIcon from '../assets/ranked_icons/Master-cropped.png';
import GrandmasterIcon from '../assets/ranked_icons/Grandmaster-cropped.png';

const iconDictionary: Record<string, string> = {
    Unranked: UnrankedIcon,
    Copper: CopperIcon,
    Bronze: BronzeIcon,
    Silver: SilverIcon,
    Gold: GoldIcon,
    Platinum: PlatinumIcon,
    Emerald: EmeraldIcon,
    Diamond: DiamondIcon,
    Master: MasterIcon,
    Grandmaster: GrandmasterIcon
}

export function returnIcon(tierName: string) {
    return iconDictionary[tierName] ?? UnrankedIcon;
}