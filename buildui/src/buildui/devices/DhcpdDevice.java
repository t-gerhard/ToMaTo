package buildui.devices;
/*
 * Copyright (c) 2002-2006 University of Utah and the Flux Group.
 * All rights reserved.
 * This file is part of the Emulab network testbed software.
 * 
 * Emulab is free software, also known as "open source;" you can
 * redistribute it and/or modify it under the terms of the GNU Affero
 * General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 * 
 * Emulab is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
 * more details, which can be found in the file AGPL-COPYING at the root of
 * the source tree.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import buildui.connectors.Connection;
import buildui.paint.Element;

import buildui.paint.PropertiesArea;

public class DhcpdDevice extends Device {

  static int num = 1;

  public DhcpdDevice (String newName) {
    super(newName, "/icons/computer.png");
  }

  public Element createAnother () {
    return new DhcpdDevice("dhcpd"+(num++)) ;
  }

  static PropertiesArea propertiesArea = new DhcpdPropertiesArea() ;

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  int ifaceNum = 0 ;

  @Override
  public Interface createInterface (Connection con) {
    return new Interface("eth"+(ifaceNum++), this, con);
  }

};
